---
status: complete
priority: p1
issue_id: "014"
tags: [code-review, security, authorization, persistence]
dependencies: []
---

# Persist Workspace Owner Across Restarts

Workspace ownership is not persisted, so restart behavior can silently reassign ownership.

## Problem Statement

After app restart, the in-memory owner registry is empty. The next caller with `x-user-role: owner` can claim any existing workspace, which allows owner takeover and locks out the original owner.

This is a merge-blocking security issue because it breaks workspace isolation and ownership guarantees.

## Findings

- `WorkspaceAccessService` keeps ownership only in `_owner_by_workspace` memory (`apps/api/auth/workspaces.py:8`).
- When `owner_id` is missing, any owner request sets ownership (`apps/api/auth/workspaces.py:15` and `apps/api/auth/workspaces.py:17`).
- Startup hydration restores only members, not owners (`apps/api/main.py:151` to `apps/api/main.py:156`).
- Local reproduction confirms takeover after restart:
  - First lifecycle: `owner-a` creates workspace and `owner-b` gets `403`.
  - After restart: `owner-b` gets `200` and then `owner-a` gets `403`.

## Proposed Solutions

### Option 1: Persist Owner in State DB (Preferred)

**Approach:** Add `workspace_owner_record(workspace_id, owner_id, created_at)` table, write owner on first workspace creation, and hydrate owner map in `lifespan`.

**Pros:**
- Fixes restart takeover at the root cause.
- Keeps authorization semantics explicit and testable.

**Cons:**
- Requires schema + migration + service changes.
- Needs migration strategy for already-created workspaces.

**Effort:** Medium

**Risk:** Low

---

### Option 2: Introduce Immutable Workspace Registry

**Approach:** Add a dedicated workspace domain object with immutable `owner_id`; all access checks query that registry.

**Pros:**
- Clear long-term model for ownership and membership.
- Eases future ACL features.

**Cons:**
- Larger refactor than immediate hotfix.
- More integration changes across endpoints/tests.

**Effort:** Large

**Risk:** Medium

---

### Option 3: Fail Closed for Unknown Owner

**Approach:** If a workspace has data but no known owner, deny access and require explicit repair/bootstrap path.

**Pros:**
- Immediate security containment.
- No silent reassignment.

**Cons:**
- Can block legitimate traffic after restart until repair runs.
- Operationally awkward without owner persistence.

**Effort:** Small

**Risk:** Medium

## Recommended Action

Implemented Option 1: persist workspace owners in the state DB and hydrate on startup.

## Technical Details

**Affected files:**
- `apps/api/auth/workspaces.py`
- `apps/api/main.py`
- `apps/api/db/state.py`
- `apps/api/db/migrations/0002_phase5_gap_closure.sql`

**Related components:**
- Workspace authorization
- Startup state hydration
- Invitation membership persistence

**Database changes (if any):**
- Add persistent owner table and startup owner restoration.

## Resources

- Reproduced locally with `uv run python` + `fastapi.testclient` against `apps.api.main:app`.
- Existing cross-workspace check: `apps/api/tests/integration/test_app_authz_integration.py`.

## Acceptance Criteria

- [x] Workspace owner is stored durably and restored on startup.
- [x] Non-owner cannot claim ownership after restart.
- [x] Original owner retains access after restart.
- [x] Regression tests cover pre-restart and post-restart authorization behavior.
- [x] Existing authz tests remain green.

## Work Log

### 2026-02-11 - Review Discovery

**By:** Codex

**Actions:**
- Reviewed ownership and startup hydration paths in `apps/api/auth/workspaces.py` and `apps/api/main.py`.
- Ran a restart reproduction with `TestClient` using a temp state DB.
- Confirmed owner takeover and owner lockout after restart.

**Learnings:**
- Membership persistence was added, but owner persistence was not.
- Current fallback ownership-claim behavior is unsafe once state survives restarts.

### 2026-02-11 - Fix Implemented

**By:** Codex

**Actions:**
- Added `workspace_owner_record` to state schema and migration.
- Updated `WorkspaceAccessService` to persist owner claims and hydrate owners from DB.
- Wired startup to initialize workspace access from durable owner records.
- Added regression coverage in:
  - `apps/api/tests/unit/test_workspace_access_unit.py`
  - `apps/api/tests/e2e/test_dual_mode_flow.py`
- Verified with:
  - `PYTHONPATH=. uv run python -m unittest apps.api.tests.unit.test_workspace_access_unit apps.api.tests.e2e.test_dual_mode_flow.DualModeFlowE2ETest.test_workspace_owner_cannot_be_reclaimed_by_different_owner_after_restart`
  - `PYTHONPATH=. uv run python -m unittest apps.api.tests.e2e.test_dual_mode_flow.DualModeFlowE2ETest.test_restart_persists_invitations_approvals_audit_and_replay`

## Notes

- Completed and validated.
