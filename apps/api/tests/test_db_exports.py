import unittest

from apps.api.db.memory_store import MemoryItem, MemoryMatch
from apps.api.db.store_postgres import PostgresMemoryStore
from apps.api.db.store_sqlite import SqliteMemoryStore


class DbExportsTest(unittest.TestCase):
    def test_db_exports_resolve_to_memory_package_types(self) -> None:
        item = MemoryItem(
            workspace_id="ws",
            agent_id="agent",
            memory_id="m1",
            content="content",
        )
        match = MemoryMatch(memory_id="m1", score=1.0, content="content")

        self.assertEqual(item.memory_id, "m1")
        self.assertEqual(match.score, 1.0)
        self.assertEqual(SqliteMemoryStore.__name__, "SqliteMemoryStore")
        self.assertEqual(PostgresMemoryStore.__name__, "PostgresMemoryStore")


if __name__ == "__main__":
    unittest.main()
