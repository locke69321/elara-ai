from apps.api.db.memory_store import MemoryItem, MemoryMatch


class PostgresMemoryStore:
    """Postgres/pgvector store stub with the same retrieval contract as SQLite."""

    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str], MemoryItem] = {}

    async def upsert_memory(
        self,
        *,
        workspace_id: str,
        agent_id: str,
        memory_id: str,
        content: str,
    ) -> MemoryItem:
        item = MemoryItem(
            workspace_id=workspace_id,
            agent_id=agent_id,
            memory_id=memory_id,
            content=content,
        )
        self._records[(workspace_id, agent_id, memory_id)] = item
        return item

    async def search(
        self,
        *,
        workspace_id: str,
        agent_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[MemoryMatch]:
        results: list[MemoryMatch] = []
        tokens = [token for token in query.lower().split() if token]

        for item in self._records.values():
            if item.workspace_id != workspace_id or item.agent_id != agent_id:
                continue

            haystack = item.content.lower()
            score = float(sum(1 for token in tokens if token in haystack))
            if score == 0.0 and tokens:
                continue

            results.append(
                MemoryMatch(memory_id=item.memory_id, score=score, content=item.content)
            )

        results.sort(key=lambda match: (-match.score, match.memory_id))
        return results[:top_k]
