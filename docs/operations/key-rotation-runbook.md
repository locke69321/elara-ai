# Key Rotation Runbook (v1)

## Scope

This runbook covers rotation for `SQLITE_CIPHER_KEY` in secure mode deployments.

## Preconditions

- Service is running with `ELARA_SQLITE_SECURE_MODE=1`.
- Operators can perform controlled restarts.
- Latest backup exists and restore has been smoke-tested.

## Rotation Procedure

1. Generate a new key in the secret manager and store it as the next version.
2. Put API writes in maintenance mode (or drain incoming traffic).
3. Create a backup snapshot of the encrypted database file.
4. Restart one instance with the new key and run health checks.
5. Run application checks:
   - `make check`
   - `make app-authz-integration`
   - `make sqlite-compat`
6. If healthy, roll the new key to all instances.
7. Re-enable writes and confirm normal operation.

## Rollback Procedure

1. Revert secret manager entry to the previous key version.
2. Restart instances with the previous key.
3. Verify health endpoints and replay critical smoke tests.
4. If data corruption is suspected, restore from the backup created before step 4.

## Post-Rotation Verification

- `docs/security/sqlite-encrypted-vector-compatibility.md` checks are green.
- API logs show no secure-mode startup failures.
- Audit/event replay continues to return deterministic sequences.
