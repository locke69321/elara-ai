---
status: complete
priority: p1
issue_id: "003"
tags: [phase3, security, audit, invitations, approvals, operability]
dependencies: ["001", "002"]
---

# Phase 3 Security Hardening + Operability

Implement the plan's Phase 3 deliverables: immutable audit trail, invitation flow, human approval workflow, self-host deploy baseline, and threat model documentation.

## Problem Statement

Phase 2 delivered core dual-mode behavior, but security/operability requirements are still incomplete. We need explicit high-impact approval controls, auditability, invitation onboarding controls, and deployment/security documentation.

## Findings

- Existing runtime has role/capability checks but high-impact approval is not enforced end-to-end.
- Audit events are represented as run events but not stored in an immutable log abstraction.
- No invitation service exists for owner-invite flow.
- No deployment compose stack or threat model doc exists yet.

## Proposed Solutions

### Option 1: In-memory security services with explicit API contracts (selected)

Implement typed in-memory services for audit, approvals, and invitations; enforce approvals in execution flow; expose endpoints and tests; add deploy/docs artifacts.

Pros:
- Delivers Phase 3 behaviors quickly
- Keeps implementation testable and easy to evolve to persistent stores

Cons:
- Persistence for these services is deferred

Effort: 4-8 hours
Risk: Medium

## Recommended Action

Implement option 1 with outside-in tests (e2e, integration, unit) and keep all quality gates passing (`make check`).

## Technical Details

Primary paths:
- `apps/api/audit/logging.py`
- `apps/api/auth/invitations.py`
- `apps/api/safety/approvals.py`
- `apps/api/main.py`
- `apps/api/agents/runtime.py`
- `deploy/docker-compose.yml`
- `docs/security/threat-model-v1.md`

## Acceptance Criteria

- [x] Immutable audit log service exists and records key actions.
- [x] Invitation service exists and supports owner invite + acceptance flow.
- [x] Approval service exists and high-impact delegations require explicit approval.
- [x] Execution path enforces approval before high-impact capability use.
- [x] SQLCipher startup enforcement is wired for secure SQLite mode.
- [x] Deploy compose baseline exists for self-host setup.
- [x] Threat model v1 document exists with concrete controls/checklist.
- [x] E2E/integration/unit tests cover new security/operability behavior.
- [x] `make check` passes with coverage >= 90%.

## Work Log

### 2026-02-11 - Todo Created

**By:** Codex

**Actions:**
- Created Phase 3 todo with dependencies on phases 1 and 2.
- Defined acceptance criteria aligned to plan Phase 3 deliverables and security gates.

**Learnings:**
- Existing runtime structure supports clean insertion of approval/audit services with minimal churn.

### 2026-02-11 - Phase 3 Implementation Complete

**By:** Codex

**Actions:**
- Implemented immutable audit service (`apps/api/audit/logging.py`) with hash-chain verification.
- Implemented invitation workflow service (`apps/api/auth/invitations.py`) with token acceptance and membership tracking.
- Implemented approvals service (`apps/api/safety/approvals.py`) and approval-required exception contract.
- Integrated approvals + audit into runtime and API flow:
  - High-impact specialist delegation now requires explicit approved request IDs.
  - Companion/execution/specialist/invitation/approval operations are audited.
- Added SQLCipher secure-mode startup enforcement in `apps/api/db/sqlite.py` and wired it in API lifespan.
- Added deploy baseline (`deploy/docker-compose.yml`) and threat model doc (`docs/security/threat-model-v1.md`).
- Expanded outside-in tests across e2e/integration/unit and API route coverage.
- Verified quality gates with `make check` (coverage 96%).

**Learnings:**
- Approval-first execution flow fits cleanly into the existing policy model when the runtime owns request generation and validation.
