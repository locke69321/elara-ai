# Self-Hosted Quickstart

## Audience

This guide is for operators running Elara locally for development or in a small trusted environment.

## Prerequisites

- macOS/Linux shell
- Python 3.13+
- Node 22+
- `uv`
- `pnpm`

## 1. Clone and Install

```bash
git clone <your-repo-url> elara-ai
cd elara-ai
make bootstrap
```

## 2. Run Quality Gate

```bash
make check
```

This verifies linting, type safety, explicit no-`Any` rules, and backend coverage >= 90%.

## 3. Start API Locally

```bash
make dev-api
```

API should be available at `http://localhost:8000`.

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

## 4. Optional Secure SQLite Mode

By default, secure mode is off in local development. To enforce SQLCipher checks at startup:

```bash
export ELARA_SQLITE_SECURE_MODE=1
export SQLITE_CIPHER_KEY='replace-with-real-key'
export SQLITE_DATABASE_URL=':memory:'
make dev-api
```

If SQLCipher capabilities are unavailable, startup fails closed.

## 5. Minimal API Walkthrough

Create a specialist:

```bash
curl -X POST http://localhost:8000/workspaces/ws1/specialists \
  -H 'content-type: application/json' \
  -H 'x-user-id: owner-1' \
  -H 'x-user-role: owner' \
  -d '{
    "id": "spec-research",
    "name": "Research Specialist",
    "prompt": "Research and summarize",
    "soul": "Focused",
    "capabilities": ["delegate", "write_memory"]
  }'
```

Execute a goal:

```bash
curl -X POST http://localhost:8000/workspaces/ws1/execution/goals \
  -H 'content-type: application/json' \
  -H 'x-user-id: owner-1' \
  -H 'x-user-role: owner' \
  -d '{"goal":"prepare a release summary"}'
```

## 6. Docker Compose Baseline

A baseline compose stack exists at `deploy/docker-compose.yml`.

Run it from `deploy/`:

```bash
cd deploy
docker compose up --build
```

Notes:
- This is a development baseline, not hardened production infra.
- API service is exposed on port `8000`.

## Troubleshooting

- `make check` fails on web typecheck:
  - Ensure `pnpm install` completed successfully.
- API startup fails in secure mode:
  - Verify `SQLITE_CIPHER_KEY` is set.
  - Disable secure mode (`ELARA_SQLITE_SECURE_MODE=0`) for local non-secure runs.
- Permission denied on specialist creation:
  - Use `x-user-role: owner`.
