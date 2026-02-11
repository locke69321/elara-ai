# Dual-Mode Core Architecture (Phase 1)

This document captures the implemented Phase 1 foundation for Elara's dual-mode platform.

## Delivered Components

- `apps/api/main.py`: FastAPI lifecycle app with health endpoint and runtime state setup.
- `apps/api/db/memory_store.py`: backend-agnostic memory store contract.
- `apps/api/db/store_sqlite.py`: SQLite adapter stub with workspace + agent scoping.
- `apps/api/db/store_postgres.py`: Postgres adapter stub with equivalent retrieval behavior.
- `apps/api/db/migrations/0001_initial.sql`: base schema including `agent_run_event` and outbox table.
- `apps/api/db/sqlite.py`: SQLCipher connection validation that fails closed.
- `apps/api/events/outbox.py`: deterministic event sequencing and replay primitives.
- `apps/api/security/crypto.py`: envelope encryption interface for sensitive memory payloads.
- `apps/web/src/routes/*`: dual-mode shell and route placeholders.
- `apps/web/src/lib/server/get-workspace.ts`: server-only data boundary example.
- `packages/contracts/*`: shared API contract types and OpenAPI seed spec.

## Execution Boundaries

- FastAPI app resources are initialized and torn down in `lifespan`.
- TanStack privileged data path is modeled with `createServerFn` in `get-workspace.ts`.
- Event stream replay contract uses `(agent_run_id, last_seq)` via outbox replay utilities.

## Data and Security Notes

- Core schema defines immutable run events keyed by `(agent_run_id, seq)`.
- SQLCipher startup path validates cipher availability and raises on insecure mode.
- Envelope crypto is isolated behind `EnvelopeCipher` to support later KMS integration.

## Next Implementation Targets

- Real database adapter implementations for SQLite vector and pgvector.
- Authn/authz and policy enforcement middleware.
- Worker execution loop wiring with persistent outbox delivery.
- Route-level tests with TanStack Start runtime harness.
