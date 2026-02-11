---
status: complete
priority: p1
issue_id: "007"
tags: [code-review, security, api, authorization]
dependencies: []
---

# Scope Approval Decisions To The Correct Workspace

## Problem Statement

Approval decisions are keyed only by `approval_id` and can be performed by any caller presenting an owner role, without validating workspace ownership. This enables cross-workspace authorization bypass.

## Findings

- `POST /approvals/{approval_id}/decision` only checks `actor.role == "owner"` and does not verify workspace ownership in `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:496`.
- `ApprovalService.decide_request` updates any matching request by ID and does not take workspace context in `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/safety/approvals.py:60`.
- Reproduction from local review session:
  - Approval created in workspace `ws-a` was successfully approved by `owner-b` (`cross_workspace_decision 200 owner-b`).

## Proposed Solutions

### Option 1: Include Workspace In Decision API And Validate Ownership

**Approach:** Move decision route under workspace scope (`/workspaces/{workspace_id}/approvals/{id}/decision`) and enforce actor membership/ownership before deciding.

**Pros:**
- Eliminates cross-tenant decision by route contract.
- Aligns decision semantics with existing workspace-scoped list/create routes.

**Cons:**
- API contract change for clients.

**Effort:** Medium

**Risk:** Low

---

### Option 2: Keep Route Shape But Enforce Workspace/Actor Validation Internally

**Approach:** Load request by ID, verify requester is owner of that request’s workspace, then allow mutation.

**Pros:**
- Backward compatible route path.
- Smaller client impact.

**Cons:**
- Hidden policy coupling and weaker route clarity.

**Effort:** Small/Medium

**Risk:** Medium

## Recommended Action

Implement Option 2 with explicit server-side authorization validation in decision flow:
only the originating owner identity for a pending approval request may decide it.

## Technical Details

**Affected files:**
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:496`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/safety/approvals.py:60`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/tests/e2e/test_dual_mode_flow.py`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/tests/unit/test_approvals_unit.py`

**Related components:**
- Approval workflow for high-impact delegation
- Workspace authorization model

**Database changes (if any):**
- Migration needed? No
- New columns/tables? None

## Resources

- **Review target:** current branch `codex/phase2-dual-mode-core`
- **Evidence:** local TestClient reproduction (`cross_workspace_decision 200 owner-b`)

## Acceptance Criteria

- [x] Approval decision is denied when requester is not authorized for the approval’s workspace.
- [x] API contract clearly includes workspace scope or equivalent server-side validation.
- [x] Tests cover cross-workspace decision attempts and expected rejection.
- [x] Existing happy-path approval flow remains green.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Traced approval decision flow from API to service layer.
- Reproduced cross-workspace approval by creating and deciding with different owner identities.
- Documented remediation options with compatibility tradeoffs.

**Learnings:**
- Global identifier mutation endpoints need explicit tenant guards even when IDs are unguessable.

### 2026-02-11 - Cross-Workspace Approval Decision Guard Implemented

**By:** Codex

**Actions:**
- Added failing API and e2e regression tests demonstrating cross-workspace owner decision attempts and expected `403`.
- Enforced authorization in `ApprovalService.decide_request` by rejecting approvers that do not match the originating approval actor identity.
- Updated API decision endpoint to translate authorization failures to `403` while keeping existing happy-path contract.
- Added unit coverage for unauthorized approver rejection in approvals service.
- Verified full repository gates with `make check` (coverage 96%).

**Learnings:**
- Binding decision authority to the approval request identity provides a clear and testable tenant-safe guard even on globally-addressed decision IDs.
