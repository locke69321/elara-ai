# Elara AI

Phase 1 foundation scaffold for an agent-native dual-mode companion and execution platform.

## Prerequisites

- `uv` (Python env + dependency manager)
- Python 3.13+
- Node 22+
- `pnpm` 10+

## Local Development Setup

```bash
make bootstrap
```

This creates/syncs `.venv` via `uv` and installs workspace dependencies via `pnpm`.

Direct equivalents:

```bash
UV_PROJECT_ENVIRONMENT=.venv uv sync --all-groups
pnpm install
```

## Common Commands

```bash
make test      # API + web tests
make lint      # API + web lint checks
make typecheck # Python + TypeScript type checks
make no-any    # fail on explicit `Any` usage in Python source
make coverage  # API coverage gate (must be >= 90%)
make check     # lint + typecheck + coverage
make dev-api   # run FastAPI on http://localhost:8000
```

Outside-in API test layers:

```bash
make api-test-e2e
make api-test-integration
make api-test-unit
```

## Project Structure

- `apps/api` FastAPI backend scaffold
- `apps/web` frontend route shell scaffold
- `apps/worker` worker scaffold
- `packages/contracts` shared contract types/OpenAPI seed
- `docs/` architecture, plan, and brainstorm documents
