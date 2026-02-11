---
status: complete
priority: p1
issue_id: "001"
tags: [phase1, fastapi, tanstack-start, architecture]
dependencies: []
---

# Phase 1 Foundation Scaffold

Implement the Phase 1 deliverables from the dual-mode core plan in a new codebase scaffold.

## Problem Statement

The repository currently contains only planning docs. Phase 1 deliverables require concrete backend/frontend/contracts scaffolding and foundational security/event/database components before feature work can start.

## Findings

- Repo contains `docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md` and brainstorm docs only.
- No existing Git repository is present at `/Users/shawnconklin/Code/Projects/elara-ai`.
- No app code exists yet for `apps/api`, `apps/web`, or shared packages.

## Proposed Solutions

### Option 1: Minimal foundation scaffold (selected)

Build the monorepo structure with a working FastAPI skeleton, basic adapter interfaces, migration SQL, event outbox sequencing utilities, and a TanStack Start route shell stub.

Pros:
- Unblocks implementation immediately
- Keeps scope aligned with Phase 1 deliverables

Cons:
- Does not complete all full v1 functional requirements

Effort: 3-5 hours
Risk: Low

## Recommended Action

Implement Option 1 with tests for deterministic event ordering and lightweight structure checks, then update plan checkboxes for completed quality/foundation criteria.

## Technical Details

Affected paths:
- `apps/api/**`
- `apps/web/**`
- `packages/contracts/**`
- `docs/architecture/dual-mode-core.md`
- `docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md`

## Resources

- `docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md`
- `docs/brainstorms/2026-02-10-agent-native-companion-platform-brainstorm.md`

## Acceptance Criteria

- [x] Monorepo directory scaffold exists for api/web/worker/contracts/agent-packs.
- [x] FastAPI app with lifespan and health route is implemented.
- [x] MemoryStore interface and initial SQLite/Postgres adapter stubs exist.
- [x] Migration SQL includes core tables and outbox with sequence constraints.
- [x] Crypto primitives provide envelope encryption helper interfaces.
- [x] Outbox publisher supports deterministic replay from `(agent_run_id, last_seq)`.
- [x] Frontend root shell and dual-mode placeholders exist.
- [x] Architecture doc exists and reflects implementation.
- [x] Backend and frontend lightweight tests pass.

## Work Log

### 2026-02-11 - Execution Start

**By:** Codex

**Actions:**
- Read selected plan and brainstorm docs.
- Identified empty codebase and selected Phase 1 scaffold scope.
- Created ready todo with concrete acceptance criteria.

**Learnings:**
- This workspace is documentation-first, so implementation starts from clean slate.

### 2026-02-11 - Phase 1 Scaffold Complete

**By:** Codex

**Actions:**
- Implemented backend skeleton: FastAPI app lifecycle, migration SQL, memory store contract/adapters, SQLCipher guard, outbox replay utility.
- Implemented frontend shell files and server-function boundary example.
- Added shared contracts and architecture documentation.
- Ran tests:
  - `python3 -m unittest discover -s apps/api/tests -t .`
  - `npm test --prefix apps/web`

**Learnings:**
- Running dependency install and tests in parallel can race; backend tests passed on rerun after install completion.

### 2026-02-11 - Repo Init and Local Dev Tooling Upgrade

**By:** Codex

**Actions:**
- Initialized Git repository (`main`) and added `.gitignore`.
- Migrated local dev workflow to `uv` + `pnpm`:
  - Added Python dependency metadata to `pyproject.toml`.
  - Added `pnpm-workspace.yaml` and workspace lockfile.
  - Updated `Makefile` bootstrap/test/lint/dev commands to use `uv run` and `pnpm`.
  - Updated `README.md` setup instructions.
- Removed legacy `pip` requirement files to avoid dependency drift.
- Re-ran validation:
  - `make bootstrap`
  - `make test`
  - `make lint`

**Learnings:**
- `pnpm` requires `pnpm-workspace.yaml` (not `workspaces` in `package.json`) for workspace mode.
