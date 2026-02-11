---
status: complete
priority: p1
issue_id: "006"
tags: [code-review, security, api, privacy]
dependencies: []
---

# Protect Agent Run Event Replay From Cross-Workspace Access

## Problem Statement

The event replay endpoint is publicly callable and not scoped to the requesting actor or workspace. Combined with predictable companion run IDs, this allows leakage of actor identifiers and memory hit metadata across tenants.

## Findings

- `GET /agent-runs/{agent_run_id}/events` does not depend on `get_actor` in `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:350`.
- Companion events use predictable `agent_run_id` format `companion-{workspace_id}` in `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/agents/runtime.py:120`.
- Companion event payload includes `actor_id` and `memory_hits` (`runtime.py:122`).
- Reproduction from local review session:
  - After sending one companion message for workspace `ws-a`, unauthenticated `GET /agent-runs/companion-ws-a/events` returned `200` with payload containing actor and memory identifiers.

## Proposed Solutions

### Option 1: Require Actor and Workspace Authorization On Replay

**Approach:** Add identity dependency to replay route and enforce requester membership/ownership for the run’s workspace before returning events.

**Pros:**
- Directly fixes current disclosure path.
- Keeps existing event model with minimal schema change.

**Cons:**
- Requires a reliable run-to-workspace ownership mapping.

**Effort:** Medium

**Risk:** Low

---

### Option 2: Make Companion Run IDs Opaque And Redact Sensitive Payload Fields

**Approach:** Switch to UUID run IDs for companion events and avoid exposing raw actor/memory IDs in event payloads.

**Pros:**
- Reduces enumeration risk and blast radius.
- Improves privacy posture for audit/event exports.

**Cons:**
- Alone, does not replace authorization checks.
- Requires client and test contract updates.

**Effort:** Medium

**Risk:** Medium

## Recommended Action

Implement Option 1 immediately (authenticated replay + run access enforcement) and add
payload hardening from Option 2 by removing direct actor/memory identifiers from replayed
companion events.

## Technical Details

**Affected files:**
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:350`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/agents/runtime.py:120`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/tests/test_api_phase2.py`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/tests/e2e/test_dual_mode_flow.py`

**Related components:**
- Outbox replay API
- Companion execution event model

**Database changes (if any):**
- Migration needed? No
- New columns/tables? None

## Resources

- **Review target:** current branch `codex/phase2-dual-mode-core`
- **Evidence:** local TestClient reproduction (`replay_without_headers 200`)

## Acceptance Criteria

- [x] Replay endpoint requires authenticated actor context.
- [x] Replay only returns runs authorized for the requester’s workspace scope.
- [x] Companion run IDs are non-enumerable or otherwise protected by authorization gates.
- [x] Event payloads do not expose unnecessary sensitive identifiers.
- [x] Regression tests cover unauthorized replay attempts.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Audited replay handler and event production path.
- Reproduced cross-workspace data visibility via predictable companion run ID.
- Documented two mitigation strategies (authorization + hardening).

**Learnings:**
- Data leakage can occur even when write endpoints are restricted if read endpoints are unauthenticated.

### 2026-02-11 - Replay Authorization and Payload Hardening Complete

**By:** Codex

**Actions:**
- Added strict replay authentication dependency requiring explicit `x-user-id` and `x-user-role` headers.
- Added runtime run-access enforcement so replay is denied (`403`) when actor identity is not authorized for the run.
- Hardened companion event payloads by removing `actor_id` and `memory_hits` from replay data and exposing only `memory_hit_count`.
- Added outside-in regression coverage:
  - E2E: unauthenticated replay rejected; cross-actor replay rejected; owner replay allowed.
  - Integration: runtime replay enforces actor authorization.
  - Unit: companion replay payload redaction contract.
- Updated existing replay tests to pass authenticated actor headers or runtime actor context.
- Verified full repository quality gate with `make check` (coverage 96%).

**Learnings:**
- Enforcing actor-aware replay at the runtime boundary lets API routes stay thin while protecting all replay call paths consistently.
