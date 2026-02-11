# Memory Controls Guide

## Memory Behavior

Companion and execution workflows write memory via the shared memory store interface.

Current domains and patterns:
- Companion messages: continuity-focused writes and retrieval hits.
- Execution flows: delegated outputs and event traces are recorded and replayable.

## Review Memory-Related Activity

### Conversation/Execution Event Replay

```bash
curl "http://localhost:8000/agent-runs/<agent_run_id>/events?last_seq=0"
```

### Audit Events

```bash
curl http://localhost:8000/workspaces/ws1/audit-events \
  -H 'x-user-id: owner-1' \
  -H 'x-user-role: owner'
```

Audit events include action, actor, outcome, and tamper-evident hash chaining.

## Redaction Guidance (Operational)

A dedicated redaction endpoint is not implemented yet. Until then:
- Treat memory payloads as sensitive operational data.
- Use conservative specialist prompts to avoid over-collection.
- Restrict write capabilities (`write_memory`) to trusted specialists.
- Prefer shorter-lived or scoped workspaces for high-sensitivity tasks.

## Encryption Controls

- Envelope crypto utilities exist in `apps/api/security/crypto.py`.
- SQLCipher secure startup checks can be enforced via:
  - `ELARA_SQLITE_SECURE_MODE=1`
  - `SQLITE_CIPHER_KEY=<key>`

## Best Practices

- Review audit events regularly after high-impact runs.
- Keep owner/member boundaries strict.
- Rotate workspace tokens/keys according to your ops policy.
