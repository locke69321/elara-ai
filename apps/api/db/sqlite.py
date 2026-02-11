import os
import sqlite3
from typing import Callable, Protocol, cast


class SqlCipherResult(Protocol):
    def fetchone(self) -> tuple[str] | None: ...


class SqlCipherConnection(Protocol):
    def execute(self, query: str, params: tuple[str] | None = None) -> SqlCipherResult: ...

    def close(self) -> None: ...


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


def enforce_sqlite_security_if_enabled(
    *,
    secure_mode_env: str | None = None,
    db_key_env: str | None = None,
    database_url_env: str | None = None,
    connect_fn: Callable[[str], SqlCipherConnection] | None = None,
) -> None:
    secure_mode = (
        secure_mode_env
        if secure_mode_env is not None
        else os.getenv("ELARA_SQLITE_SECURE_MODE", "0")
    )
    if secure_mode != "1":
        return

    db_key = db_key_env if db_key_env is not None else os.getenv("SQLITE_CIPHER_KEY")
    if not db_key:
        raise RuntimeError("SQLITE_CIPHER_KEY must be set when secure mode is enabled")

    database_url = (
        database_url_env
        if database_url_env is not None
        else os.getenv("SQLITE_DATABASE_URL", ":memory:")
    )
    if database_url is None:
        database_url = ":memory:"

    if connect_fn is None:
        def sqlite_connect(url: str) -> SqlCipherConnection:
            return cast(SqlCipherConnection, sqlite3.connect(url))

        connect_fn = sqlite_connect

    connection = connect_sqlcipher(connect_fn, database_url, db_key)
    connection.close()
