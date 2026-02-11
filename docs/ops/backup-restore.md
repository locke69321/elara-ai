# Backup and Restore Runbook

## Scope

This runbook covers SQLite (default) and PostgreSQL variants for backup/restore workflows.

## SQLite Variant

### Backup

Assuming DB file path `SQLITE_DATABASE_URL=/data/elara.db`:

```bash
mkdir -p backups
cp /data/elara.db backups/elara-$(date +%Y%m%d-%H%M%S).db
```

If running via compose volume, run from the API container or mount path.

### Restore

```bash
cp backups/elara-<timestamp>.db /data/elara.db
```

Then restart API service.

### Validation

```bash
curl http://localhost:8000/health
curl http://localhost:8000/workspaces/ws1/audit-events \
  -H 'x-user-id: owner-1' \
  -H 'x-user-role: owner'
```

## PostgreSQL Variant (When Enabled)

### Backup

```bash
pg_dump "$DATABASE_URL" > backups/elara-$(date +%Y%m%d-%H%M%S).sql
```

### Restore

```bash
psql "$DATABASE_URL" < backups/elara-<timestamp>.sql
```

## Backup Cadence Recommendation

- Development: daily snapshot.
- Small trusted production: hourly incremental + daily full.
- Retention: 14 days minimum (tune by compliance requirements).

## Restore Drill Checklist

- [ ] Restore into a non-production environment first.
- [ ] API starts successfully.
- [ ] Specialist list endpoint responds.
- [ ] Invitation and approval endpoints respond.
- [ ] Audit chain verifies for key workspaces.

## Key Rotation and Secure Mode Notes

- Secure SQLite mode requires `SQLITE_CIPHER_KEY` when enabled.
- Store keys in your secret manager, not source control.
- Document key ownership, rotation frequency, and rollback procedure.

## Known Limitations

- Current invitation/approval/audit implementations are in-memory service layers in v1 scaffolding.
- For production durability, persist these services in your database layer before rollout.
