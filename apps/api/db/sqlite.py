from typing import Callable, Protocol


class SqlCipherResult(Protocol):
    def fetchone(self) -> tuple[str] | None: ...


class SqlCipherConnection(Protocol):
    def execute(self, query: str, params: tuple[str] | None = None) -> SqlCipherResult: ...


def validate_sqlcipher_connection(connection: SqlCipherConnection) -> None:
    cipher_version = connection.execute("PRAGMA cipher_version;").fetchone()
    if not cipher_version or not cipher_version[0]:
        raise RuntimeError(
            "SQLCipher is not active; refusing to start insecure SQLite mode"
        )


def connect_sqlcipher(
    connect_fn: Callable[[str], SqlCipherConnection],
    database_url: str,
    db_key: str,
) -> SqlCipherConnection:
    connection = connect_fn(database_url)
    connection.execute("PRAGMA key = ?;", (db_key,))
    connection.execute("PRAGMA foreign_keys = ON;")
    validate_sqlcipher_connection(connection)
    return connection
