import os
import tempfile

from apps.api.db.sqlite import enforce_sqlite_security_if_enabled
from apps.api.memory import SqliteMemoryStore


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        database_path = f"{tmp_dir}/compat.sqlite3"
        os.environ["ELARA_SQLITE_SECURE_MODE"] = "0"
        os.environ["ELARA_STATE_DB_PATH"] = database_path

        enforce_sqlite_security_if_enabled(secure_mode_env="0")

        store = SqliteMemoryStore(database_path=database_path)

        import asyncio

        async def run() -> None:
            await store.upsert_memory(
                workspace_id="ws-compat",
                agent_id="agent-compat",
                memory_id="m-1",
                content="compatibility vector baseline",
                embedding=[0.1, 0.2, 0.3],
            )
            matches = await store.search(
                workspace_id="ws-compat",
                agent_id="agent-compat",
                query="vector baseline",
                top_k=1,
            )
            if len(matches) != 1:
                raise RuntimeError("expected one retrieval result for compatibility check")

        asyncio.run(run())

    print("SQLite secure-mode compatibility and vector retrieval checks passed")


if __name__ == "__main__":
    main()
