import unittest

from apps.api.db.sqlite import connect_sqlcipher, enforce_sqlite_security_if_enabled


class FakeCursor:
    def __init__(self, value: str):
        self._value = value

    def fetchone(self) -> tuple[str]:
        return (self._value,)


class FakeConnection:
    def __init__(self, cipher_version: str):
        self.cipher_version = cipher_version
        self.commands: list[tuple[str, tuple | None]] = []

    def execute(self, query: str, params: tuple | None = None):
        self.commands.append((query, params))
        if query == "PRAGMA cipher_version;":
            return FakeCursor(self.cipher_version)
        return self

    def close(self) -> None:
        return None


class SqlCipherConnectionTest(unittest.TestCase):
    def test_connection_validates_cipher_version(self) -> None:
        connection = FakeConnection(cipher_version="4.5.0")

        opened = connect_sqlcipher(lambda _: connection, "memory.db", "secret")

        self.assertIs(opened, connection)
        self.assertIn(("PRAGMA key = ?;", ("secret",)), connection.commands)

    def test_connection_fails_closed_when_cipher_missing(self) -> None:
        connection = FakeConnection(cipher_version="")

        with self.assertRaises(RuntimeError):
            connect_sqlcipher(lambda _: connection, "memory.db", "secret")

    def test_secure_mode_requires_key(self) -> None:
        with self.assertRaises(RuntimeError):
            enforce_sqlite_security_if_enabled(
                secure_mode_env="1",
                db_key_env="",
                database_url_env="memory.db",
                connect_fn=lambda _: FakeConnection(cipher_version="4.5.0"),
            )

    def test_secure_mode_connects_when_enabled(self) -> None:
        connection = FakeConnection(cipher_version="4.5.0")
        enforce_sqlite_security_if_enabled(
            secure_mode_env="1",
            db_key_env="secret",
            database_url_env="memory.db",
            connect_fn=lambda _: connection,
        )
        self.assertIn(("PRAGMA key = ?;", ("secret",)), connection.commands)


if __name__ == "__main__":
    unittest.main()
