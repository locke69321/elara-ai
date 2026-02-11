# SQLite Encrypted Vector Compatibility

## Goal

Demonstrate that the v1 SQLite runtime remains compatible with secure startup checks and memory retrieval operations that include embedding metadata.

## Compatibility Matrix

| Mode | Secure Startup Check | Memory Retrieval Contract | Result |
|------|----------------------|---------------------------|--------|
| Local dev (`ELARA_SQLITE_SECURE_MODE=0`) | Bypassed intentionally | Deterministic top-k ordering + workspace/agent scoping | Pass |
| Secure mode (`ELARA_SQLITE_SECURE_MODE=1`, SQLCipher available) | Enforced by `enforce_sqlite_security_if_enabled` | Same retrieval contract as local mode | Pass (environment-dependent) |
| Secure mode without key | Fails closed | Runtime startup blocked | Pass (expected failure) |

## Verification Command

```bash
PYTHONPATH=. uv run python scripts/compat/check_sqlite_vector_compat.py
```

## Evidence

- Compatibility check script: `scripts/compat/check_sqlite_vector_compat.py`
- Secure startup enforcement: `apps/api/db/sqlite.py`
- Memory store dimension/scoping contract: `apps/api/memory/store_sqlite.py`
