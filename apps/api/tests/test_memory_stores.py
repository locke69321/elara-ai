import unittest

from apps.api.db.store_postgres import PostgresMemoryStore
from apps.api.db.store_sqlite import SqliteMemoryStore


class MemoryStoreContractTest(unittest.IsolatedAsyncioTestCase):
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
