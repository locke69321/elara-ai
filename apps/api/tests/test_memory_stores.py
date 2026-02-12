import os
import tempfile
import unittest

from apps.api.db.store_postgres import PostgresMemoryStore
from apps.api.db.store_sqlite import SqliteMemoryStore


class MemoryStoreContractTest(unittest.IsolatedAsyncioTestCase):
    async def test_sqlite_and_postgres_backends_return_parity_for_top_k_and_ordering(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sqlite_path = os.path.join(tmp_dir, "sqlite-memory.sqlite3")
            postgres_path = os.path.join(tmp_dir, "postgres-memory.sqlite3")
            sqlite_store = SqliteMemoryStore(database_path=sqlite_path)
            postgres_store = PostgresMemoryStore(database_path=postgres_path)

            for store in (sqlite_store, postgres_store):
                await store.upsert_memory(
                    workspace_id="ws-parity",
                    agent_id="agent-parity",
                    memory_id="m-low",
                    content="alpha beta",
                )
                await store.upsert_memory(
                    workspace_id="ws-parity",
                    agent_id="agent-parity",
                    memory_id="m-high",
                    content="alpha alpha beta",
                )
                await store.upsert_memory(
                    workspace_id="ws-parity",
                    agent_id="agent-parity",
                    memory_id="m-other",
                    content="beta",
                )

            sqlite_results = await sqlite_store.search(
                workspace_id="ws-parity",
                agent_id="agent-parity",
                query="alpha beta",
                top_k=2,
            )
            postgres_results = await postgres_store.search(
                workspace_id="ws-parity",
                agent_id="agent-parity",
                query="alpha beta",
                top_k=2,
            )

            self.assertEqual(
                [item.memory_id for item in sqlite_results],
                [item.memory_id for item in postgres_results],
            )

    async def test_dimension_mismatch_raises_for_existing_memory_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sqlite_path = os.path.join(tmp_dir, "sqlite-dimension.sqlite3")
            store = SqliteMemoryStore(database_path=sqlite_path)

            await store.upsert_memory(
                workspace_id="ws-dimension",
                agent_id="agent-dimension",
                memory_id="m-1",
                content="first",
                embedding=[0.1, 0.2, 0.3],
            )

            with self.assertRaises(ValueError):
                await store.upsert_memory(
                    workspace_id="ws-dimension",
                    agent_id="agent-dimension",
                    memory_id="m-1",
                    content="second",
                    embedding=[0.1, 0.2],
                )

    async def test_sqlite_store_applies_workspace_and_agent_scope(self) -> None:
        store = SqliteMemoryStore()
        await store.upsert_memory(
            workspace_id="ws-1",
            agent_id="agent-1",
            memory_id="m1",
            content="alpha memory",
        )
        await store.upsert_memory(
            workspace_id="ws-2",
            agent_id="agent-1",
            memory_id="m2",
            content="alpha memory",
        )

        matches = await store.search(
            workspace_id="ws-1",
            agent_id="agent-1",
            query="alpha",
        )

        self.assertEqual([match.memory_id for match in matches], ["m1"])

    async def test_postgres_store_applies_workspace_and_agent_scope(self) -> None:
        store = PostgresMemoryStore()
        await store.upsert_memory(
            workspace_id="ws-1",
            agent_id="agent-2",
            memory_id="m1",
            content="project zephyr",
        )
        await store.upsert_memory(
            workspace_id="ws-1",
            agent_id="agent-3",
            memory_id="m2",
            content="project zephyr",
        )

        matches = await store.search(
            workspace_id="ws-1",
            agent_id="agent-2",
            query="zephyr",
        )

        self.assertEqual([match.memory_id for match in matches], ["m1"])


if __name__ == "__main__":
    unittest.main()
