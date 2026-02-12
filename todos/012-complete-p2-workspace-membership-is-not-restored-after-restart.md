---
status: complete
priority: p2
issue_id: "012"
tags: [code-review, authorization, persistence, api]
dependencies: []
---

# Restore Workspace Membership Access After Service Restart

## Problem Statement

Accepted invitations persist in SQLite, but workspace authorization state is kept only in-memory. After process restart, previously accepted members lose access to their workspace until re-added in memory, creating user-visible authorization regressions.

## Findings

- `InvitationService` persists memberships to `workspace_membership_record` (`apps/api/auth/invitations.py:220`).
- `WorkspaceAccessService` stores owner/member mappings only in memory (`apps/api/auth/workspaces.py:7`).
- App startup initializes a fresh `WorkspaceAccessService` with no hydration (`apps/api/main.py:151`).
- Repro (local):
  - accept invitation as member;
  - member can access during same runtime;
  - restart app;
  - same member receives `403 actor is not authorized for this workspace`.

## Proposed Solutions

### Option 1: Hydrate WorkspaceAccessService on Startup

**Approach:** On app lifespan startup, load persisted memberships and owner mappings from state DB into `WorkspaceAccessService`.

**Pros:**
- Minimal changes to existing API/auth flow.
- Fixes restart regression quickly.

**Cons:**
- Keeps dual sources of truth (DB + in-memory cache).

**Effort:** Small

**Risk:** Low

---

### Option 2: Make WorkspaceAccessService Database-Backed

**Approach:** Move authorization checks to DB queries (or repository abstraction) rather than in-memory maps.

**Pros:**
- Single source of truth.
- Better resilience across restarts and multiple app instances.

**Cons:**
- Broader refactor touching auth paths.

**Effort:** Medium

**Risk:** Medium

---

### Option 3: Hybrid Cache with Explicit Invalidation

**Approach:** DB as source of truth plus cache layer for hot paths; refresh on membership/owner changes.

**Pros:**
- Preserves performance with correctness.
- Scales better for multi-instance deploys.

**Cons:**
- More complexity than needed immediately.

**Effort:** Large

**Risk:** Medium

## Recommended Action

Implemented Option 1 (startup hydration) by loading persisted memberships into `WorkspaceAccessService` during app lifespan initialization.

## Technical Details

**Affected files:**
- `apps/api/auth/workspaces.py:7`
- `apps/api/main.py:151`
- `apps/api/auth/invitations.py:220`

**Related components:**
- Invitation accept endpoint: `apps/api/main.py:521`
- Workspace authorization checks: `apps/api/main.py:259`

**Database changes (if any):**
- None required for Option 1/2 if current schema is reused.

## Resources

- **Review target:** Working tree on `codex/phase5-gap-closure`
- **Related tests:** `apps/api/tests/e2e/test_dual_mode_flow.py`

## Acceptance Criteria

- [x] Members accepted before restart retain workspace access after restart.
- [x] Owner authorization behavior remains unchanged.
- [x] E2E test covers invitation acceptance followed by restart and member access.
- [x] No new cross-workspace authorization regressions.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Traced invitation persistence and workspace authorization code paths.
- Ran a local restart repro using `TestClient` with file-backed state DB.
- Confirmed 403 regression for previously accepted member after restart.

**Learnings:**
- Membership persistence exists, but authorization hydration does not.
- Restart behavior currently diverges from expected persistent auth semantics.

### 2026-02-11 - Remediation Completed

**By:** Codex

**Actions:**
- Added startup hydration in `apps/api/main.py` to restore workspace members from persisted invitation memberships.
- Extended invitation service membership listing to support loading all memberships for startup hydration.
- Extended restart e2e flow to assert invited member access is retained after process restart.
- Added unit coverage for listing memberships across workspaces.
- Ran `make check` to validate lint, typecheck, and coverage gates.

## Notes

- This should be fixed before relying on invitation-based onboarding in persistent deployments.
