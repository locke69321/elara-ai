---
module: Authentication
date: 2026-02-11
problem_type: security_issue
component: authentication
symptoms:
  - "Owners could read invitations, approvals, audit events, and specialists from another workspace by guessing workspace_id."
  - "GET /workspaces/{workspace_id}/specialists returned data without actor headers."
  - "Members could trigger high-impact execution approval flows that could never be approved."
root_cause: missing_permission
resolution_type: code_fix
severity: high
tags: [tenant-isolation, authorization, high-impact, approvals, fastapi]
---

# Troubleshooting: Cross-Workspace Leakage And Member High-Impact Delegation Authorization

## Problem
Workspace-scoped routes were not enforcing tenant ownership/membership consistently. This enabled cross-workspace reads for owner-role users and exposed a deadlocked approval path where member high-impact delegation was requested but could not be decided.

## Environment
- Module: Authentication and authorization boundaries
- Runtime: FastAPI API service (`apps/api`)
- Affected Components: workspace route authorization, policy engine, execution approval flow
- Date solved: 2026-02-11

## Symptoms
- Cross-owner reads returned `200` for foreign workspace specialist/invitation/approval/audit endpoints.
- `GET /workspaces/{workspace_id}/specialists` returned `200` without identity headers.
- Member execution against high-impact specialist returned `409` with approval request, but owner decision returned `403` and member decision was also `403`.

## What Didn't Work

**Attempted Solution 1:** Role-only checks (`owner`/`member`) at endpoints.
- **Why it failed:** Role checks without workspace ownership/membership checks do not enforce tenant isolation.

**Attempted Solution 2:** Keep member high-impact flow as approval-required.
- **Why it failed:** Existing decision policy only allows requester-owned decisions and route-level decision requires owner role, creating a deadlock for member requests.

## Solution
Introduce explicit workspace access authorization and deny member high-impact delegation before approval creation.

**Code changes**:
```python
# apps/api/auth/workspaces.py
class WorkspaceAccessService:
    def ensure_workspace_access(self, *, workspace_id: str, actor: ActorContext) -> None:
        ...

# apps/api/main.py
@app.get("/workspaces/{workspace_id}/specialists")
async def list_specialists(..., actor: ActorContext = Depends(get_actor), ...):
    authorize_workspace_access(workspace_id=workspace_id, actor=actor, workspace_access=workspace_access)

# apps/api/agents/policy.py
if actor.role == "member" and capabilities.intersection(HIGH_IMPACT_CAPABILITIES):
    return PolicyDecision(allowed=False, reason="members cannot delegate high-impact capabilities")
```

**Runtime behavior update**:
- `AgentRuntime.execute_goal` now raises `PermissionError` for member high-impact denial cases, producing API `403` instead of creating unresolvable approvals.

**Route hardening**:
- Workspace authorization now enforced on specialists, companion, execution, invitations, approvals, and audit listing routes.
- Invitation acceptance adds the user to workspace member access registry.

## Why This Works
1. **Tenant boundary enforcement:** Each workspace action now verifies actor authorization against workspace ownership/membership, not role alone.
2. **Deadlock removal:** Members are blocked from high-impact delegation before approval request creation, so impossible decision workflows are never created.
3. **Consistent API semantics:** Unauthorized access returns `403`; missing identity headers return `401`.

## Prevention
- Require workspace authorization checks for every `/workspaces/{workspace_id}/...` route.
- Add explicit tests for cross-workspace owner reads and headerless access on read routes.
- Treat high-impact capability delegation policy as role-conditional at policy-engine level.
- Keep integration tests that verify no unresolvable approval states can be created.

## Related Issues
- See also: [raw-invitation-tokens-in-audit-metadata-authentication-20260210.md](./raw-invitation-tokens-in-audit-metadata-authentication-20260210.md)
