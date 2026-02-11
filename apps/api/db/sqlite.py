from typing import Any, Callable


def validate_sqlcipher_connection(connection: Any) -> None:
    cipher_version = connection.execute("PRAGMA cipher_version;").fetchone()
    if not cipher_version or not cipher_version[0]:
        raise RuntimeError(
            "SQLCipher is not active; refusing to start insecure SQLite mode"
        )


def connect_sqlcipher(
    connect_fn: Callable[[str], Any],
    database_url: str,
    db_key: str,
) -> Any:
    connection = connect_fn(database_url)
    connection.execute("PRAGMA key = ?;", (db_key,))
    connection.execute("PRAGMA foreign_keys = ON;")
    validate_sqlcipher_connection(connection)
    return connection
