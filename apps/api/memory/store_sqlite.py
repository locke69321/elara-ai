import json
import sqlite3
from datetime import datetime, timezone

from apps.api.db.state import connect_state_db
from apps.api.memory.store_base import MemoryItem, MemoryMatch


class SqliteMemoryStore:
    """Memory store with deterministic retrieval contract and optional SQLite persistence."""

    def __init__(
        self,
        *,
        database_path: str | None = None,
        connection: sqlite3.Connection | None = None,
        backend_name: str = "sqlite",
    ) -> None:
        self._connection = connection
        self._owns_connection = False
        if self._connection is None and database_path is not None:
            self._connection = connect_state_db(database_path)
            self._owns_connection = True
        self._backend_name = backend_name
        self._records: dict[tuple[str, str, str], MemoryItem] = {}
        self._embedding_dim_by_key: dict[tuple[str, str, str], int] = {}

    def close(self) -> None:
        if self._connection is None or not self._owns_connection:
            return
        self._connection.close()
        self._connection = None

    def __del__(self) -> None:
        self.close()

    async def upsert_memory(
        self,
        *,
        workspace_id: str,
        agent_id: str,
        memory_id: str,
        content: str,
        embedding: list[float] | None = None,
        embedding_model: str = "text-embedding-3-small",
    ) -> MemoryItem:
        embedding_dim = len(embedding) if embedding is not None else 0
        item = MemoryItem(
            workspace_id=workspace_id,
            agent_id=agent_id,
            memory_id=memory_id,
            content=content,
        )

        key = (workspace_id, agent_id, memory_id)
        if self._connection is None:
            existing_dim = self._embedding_dim_by_key.get(key, 0)
            if existing_dim > 0 and embedding_dim > 0 and existing_dim != embedding_dim:
                raise ValueError("embedding dimension mismatch for existing memory id")
            self._records[key] = item
            self._embedding_dim_by_key[key] = (
                existing_dim if existing_dim > 0 and embedding_dim == 0 else embedding_dim
            )
            return item

        cursor = self._connection.execute(
            """
            select embedding_dim
            from memory_record
            where backend = ? and workspace_id = ? and agent_id = ? and memory_id = ?
            """,
            (self._backend_name, workspace_id, agent_id, memory_id),
        )
        row = cursor.fetchone()
        existing_dim = 0 if row is None else int(row[0])
        if existing_dim > 0 and embedding_dim > 0 and existing_dim != embedding_dim:
            raise ValueError("embedding dimension mismatch for existing memory id")

        persisted_dim = existing_dim if existing_dim > 0 and embedding_dim == 0 else embedding_dim
        now = datetime.now(timezone.utc).isoformat()
        self._connection.execute(
            """
            insert into memory_record (
              backend, workspace_id, agent_id, memory_id, content,
              embedding_model, embedding_dim, embedding_json, created_at, updated_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            on conflict(backend, workspace_id, agent_id, memory_id)
            do update set
              content = excluded.content,
              embedding_model = excluded.embedding_model,
              embedding_dim = excluded.embedding_dim,
              embedding_json = excluded.embedding_json,
              updated_at = excluded.updated_at
            """,
            (
                self._backend_name,
                workspace_id,
                agent_id,
                memory_id,
                content,
                embedding_model,
                persisted_dim,
                None if embedding is None else json.dumps(embedding),
                now,
                now,
            ),
        )
        self._connection.commit()
        return item

    async def search(
        self,
        *,
        workspace_id: str,
        agent_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[MemoryMatch]:
        if top_k <= 0:
            return []

        if self._connection is not None:
            cursor = self._connection.execute(
                """
                select memory_id, content
                from memory_record
                where backend = ? and workspace_id = ? and agent_id = ?
                """,
                (self._backend_name, workspace_id, agent_id),
            )
            rows = cursor.fetchall()
            records = [
                MemoryItem(
                    workspace_id=workspace_id,
                    agent_id=agent_id,
                    memory_id=str(row[0]),
                    content=str(row[1]),
                )
                for row in rows
            ]
        else:
            records = [
                item
                for item in self._records.values()
                if item.workspace_id == workspace_id and item.agent_id == agent_id
            ]

        results: list[MemoryMatch] = []
        tokens = [token for token in query.lower().split() if token]
        for item in records:
            haystack = item.content.lower()
            score = float(sum(1 for token in tokens if token in haystack))
            if score == 0.0 and tokens:
                continue

            results.append(
                MemoryMatch(memory_id=item.memory_id, score=score, content=item.content)
            )

        results.sort(key=lambda match: (-match.score, match.memory_id))
        return results[:top_k]
