---
status: complete
priority: p1
issue_id: "002"
tags: [phase2, agents, policy, memory, frontend]
dependencies: ["001"]
---

# Phase 2 Dual-Mode Core + Agent Team

Implement the plan's Phase 2 deliverables across API runtime/policy/memory and dual-mode frontend workflows.

## Problem Statement

Phase 1 established scaffolding only. The product still lacks runtime behavior for companion continuity, execution delegation, specialist configuration controls, and event replay integration needed for functional dual-mode usage.

## Findings

- Foundation exists for FastAPI, outbox sequencing, and route placeholders.
- No agent runtime orchestration layer exists yet.
- No policy engine enforces owner/member specialist editing boundaries.
- Companion/execution routes are static and not connected to runtime behavior.

## Proposed Solutions

### Option 1: Minimal but complete Phase 2 vertical slice (selected)

Add a policy-gated runtime service and API endpoints for companion chat, specialist management, goal execution, and replay. Upgrade frontend route modules with concrete data flow placeholders and workflow affordances.

Pros:
- Ships plan-aligned behavior quickly
- Keeps scope bounded to Phase 2 acceptance goals
- Enables deterministic testing of delegation/replay

Cons:
- Uses in-memory stubs rather than persistent DB-backed runtime

Effort: 4-8 hours
Risk: Medium

## Recommended Action

Implement Option 1 with explicit tests for policy constraints, delegation attribution, and replay ordering. Keep interfaces forward-compatible with persistent adapters.

## Technical Details

Likely paths:
- `apps/api/agents/runtime.py`
- `apps/api/agents/policy.py`
- `apps/api/memory/store_*.py`
- `apps/api/main.py`
- `apps/api/tests/test_*.py`
- `apps/web/src/routes/companion.tsx`
- `apps/web/src/routes/execution.tsx`
- `apps/web/src/routes/agent-studio.tsx`
- `apps/web/tests/structure.test.mjs`

## Resources

- `docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md`
- `todos/001-complete-p1-phase1-foundation-scaffold.md`

## Acceptance Criteria

- [x] Agent runtime can process companion messages with continuity memory hits.
- [x] Execution mode delegates goal subtasks to eligible specialists with per-agent attribution.
- [x] Policy engine prevents invited members from creating/editing specialist definitions.
- [x] Common memory API remains backend-agnostic through memory adapter interfaces.
- [x] Event replay API resumes from `(agent_run_id, last_seq)` deterministically.
- [x] Frontend dual-mode routes reflect companion/execution/studio workflows beyond static placeholders.
- [x] Backend and frontend tests cover new behavior and pass.

## Work Log

### 2026-02-11 - Todo Created

**By:** Codex

**Actions:**
- Created Phase 2 ready todo with explicit dependency on issue `001`.
- Defined acceptance criteria aligned with plan Phase 2 success criteria.

**Learnings:**
- Tracking Phase 2 separately keeps plan execution auditable and avoids scope blur with repository setup tasks.

### 2026-02-11 - Phase 2 Implementation Complete

**By:** Codex

**Actions:**
- Implemented policy-gated runtime orchestration (`apps/api/agents/runtime.py`, `apps/api/agents/policy.py`).
- Added backend memory adapter package in `apps/api/memory/` and aligned legacy `apps/api/db/store_*.py` imports.
- Wired FastAPI endpoints for specialist management, companion messaging, execution goals, and event replay in `apps/api/main.py`.
- Expanded OpenAPI and shared contracts for phase-2 routes and payloads in `packages/contracts/`.
- Upgraded companion/execution/agent-studio routes with workflow-oriented shells.
- Added backend tests for policy, runtime, and API endpoints.
- Validated with `make bootstrap`, `make test`, and `make lint`.

**Learnings:**
- `fastapi.testclient` requires explicit `httpx` in dev dependencies for this setup.
