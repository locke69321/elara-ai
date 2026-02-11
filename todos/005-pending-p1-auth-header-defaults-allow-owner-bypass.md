---
status: complete
priority: p1
issue_id: "005"
tags: [code-review, security, api, auth]
dependencies: []
---

# Remove Implicit Owner Fallback In Actor Dependency

## Problem Statement

The API currently treats missing identity headers as an authenticated owner request. This makes privileged endpoints callable without authentication and effectively bypasses authorization.

## Findings

- `get_actor` defaults `x-user-id` to `"local-owner"` and `x-user-role` to `"owner"` in `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:219`.
- Privileged routes (`POST /workspaces/{workspace_id}/specialists`, invitation and approval routes) rely on `get_actor`, so missing headers are accepted as owner.
- Reproduction from local review session:
  - `POST /workspaces/ws-a/specialists` without any headers returned `201`.

## Proposed Solutions

### Option 1: Require Explicit Identity Headers

**Approach:** Remove default header values and fail with `401/400` when either header is missing.

**Pros:**
- Smallest patch with immediate risk reduction.
- Preserves current route shape and tests with minimal updates.

**Cons:**
- Still relies on caller-supplied headers and no signature/session validation.

**Effort:** Small

**Risk:** Low

---

### Option 2: Replace Header Identity With Verified Auth Context

**Approach:** Introduce real authentication (JWT/session) and derive actor from verified token claims.

**Pros:**
- Correct long-term security model.
- Enables principled membership/tenant checks.

**Cons:**
- Larger change touching middleware, config, and tests.

**Effort:** Large

**Risk:** Medium

## Recommended Action

Implement Option 1 immediately by requiring explicit identity headers in the shared actor dependency,
and enforce this uniformly across actor-gated routes.

## Technical Details

**Affected files:**
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:219`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/tests/test_api_phase2.py`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/tests/e2e/test_dual_mode_flow.py`

**Related components:**
- FastAPI dependency injection for identity context
- Authorization gates in specialists/invitations/approvals endpoints

**Database changes (if any):**
- Migration needed? No
- New columns/tables? None

## Resources

- **Review target:** current branch `codex/phase2-dual-mode-core`
- **Evidence:** local TestClient reproduction (`create_without_headers 201`)

## Acceptance Criteria

- [x] Requests missing identity context no longer receive implicit owner privileges.
- [x] Privileged endpoints reject unauthenticated requests.
- [x] Unit/API tests cover missing-header and malformed-header cases.
- [x] `make check` remains green.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Reviewed actor dependency and route authorization usage.
- Reproduced unauthenticated privileged write (`POST /specialists` returning `201`).
- Documented mitigation options and testing requirements.

**Learnings:**
- Role checks alone are ineffective while identity can be defaulted by framework parameters.

### 2026-02-11 - Header Auth Fallback Removed

**By:** Codex

**Actions:**
- Removed implicit owner fallback from `get_actor` by requiring explicit `x-user-id` and `x-user-role` headers.
- Unified replay authorization dependency to use `get_actor`, keeping actor-gated routes on one shared auth rule.
- Added failing-then-passing regression tests proving missing headers are rejected for privileged routes:
  - API test for specialist creation without headers (`401`).
  - E2E test for specialist creation without headers (`401`).
- Confirmed malformed role behavior remains enforced (`400`) via existing API coverage.
- Verified repository quality gates with `make check` (coverage 96%).

**Learnings:**
- Centralizing header validation in a single dependency prevents privilege bypass regressions across multiple endpoints.
