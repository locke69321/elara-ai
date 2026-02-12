import sqlite3

from apps.api.memory.store_sqlite import SqliteMemoryStore


class PostgresMemoryStore(SqliteMemoryStore):
    """Postgres/pgvector-compatible contract using the shared deterministic retrieval behavior."""

    def __init__(
        self,
        *,
        database_path: str | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        super().__init__(
            database_path=database_path,
            connection=connection,
            backend_name="postgres",
        )
