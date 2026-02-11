# Threat Model v1

## Scope

This threat model covers the v1 self-hosted dual-mode runtime implemented in `apps/api`.

In scope:
- Role-based access controls for owner/member user roles
- Specialist capability boundaries and high-impact approval flow
- Invitation-based onboarding flow
- Audit event integrity guarantees
- SQLite secure mode startup checks

Out of scope (v2+):
- Enterprise SSO and external IdP integration
- Multi-tenant org administration beyond owner/member
- Hardware-backed key management systems

## Assets

- Memory records and conversation continuity payloads
- Specialist definitions (prompt, soul, capabilities)
- Delegation and approval decision history
- Invitation tokens and membership bindings
- Audit logs for sensitive operations

## Trust Boundaries

- API caller -> FastAPI route handlers
- Runtime orchestration -> approval/policy/audit services
- App process -> SQLite/SQLCipher runtime capabilities
- Owner-only admin operations -> invitation and approval decisions

## Primary Threats and Controls

1. Unauthorized specialist modification by non-owner users
- Threat: member escalates behavior by editing specialist capabilities.
- Control: `PolicyEngine.can_edit_specialists` enforces owner-only writes.
- Validation: e2e and api tests assert `403` for member edits.

2. Unsafe high-impact actions without explicit approval
- Threat: delegated specialists execute external or tooling actions automatically.
- Control: owners require explicit approval (`ApprovalRequiredError`) for high-impact delegation, while members are denied high-impact delegation outright.
- Validation: e2e/integration tests assert owner approval-resume behavior and member `403` denial for high-impact requests.

3. Audit log tampering
- Threat: attackers alter action history to hide changes.
- Control: append-only audit log with per-workspace hash chain (`previous_hash` + payload hash).
- Validation: unit test verifies chain fails when event content is tampered.

4. Insecure SQLite startup in secure deployments
- Threat: deployment expects encrypted SQLite but starts plaintext.
- Control: startup check `enforce_sqlite_security_if_enabled` fails closed when secure mode is enabled without SQLCipher/key.
- Validation: unit tests cover key-missing and successful secure-mode validation.

5. Invitation abuse or replay
- Threat: reused or expired invitation token grants unintended membership.
- Control: invitation service marks tokens accepted once and rejects reused/expired tokens.
- Control: audit metadata records token fingerprints only; raw bearer invitation tokens are never logged.
- Validation: unit tests verify duplicate acceptance is rejected.

6. Cross-workspace read leakage
- Threat: owner-role users read specialist/invitation/approval/audit data from foreign workspaces by guessing `workspace_id`.
- Control: workspace access service enforces workspace ownership/membership checks on all workspace-scoped routes.
- Validation: api/e2e tests assert cross-owner reads return `403` across specialists, invitations, approvals, and audit events.

## Security Checklist (Pre-Release)

- [x] Authz checks enforce owner-only specialist edits
- [x] High-impact delegation requires explicit approval
- [x] Members are denied high-impact specialist delegation
- [x] Approval decisions are auditable with actor and timestamp
- [x] Invitation creation and acceptance are auditable
- [x] Invitation audit metadata redacts bearer tokens via fingerprints
- [x] Workspace-scoped reads enforce tenant isolation
- [x] SQLCipher secure-mode startup guard exists and fails closed
- [x] Lint/typecheck/no-any/coverage gates pass via `make check`
- [x] External tool allowlist enforcement finalized for production providers
- [x] Key rotation runbook finalized for operator docs

## Residual Risks

- Services are currently in-memory; persistence hardening is still required.
- Approval semantics are explicit but not yet bound to a durable identity provider.
- Audit chain is tamper-evident in-process; append-only external storage is recommended for production.

## Implementation Evidence

- Tool allowlist gate: `apps/api/agents/policy.py` and `apps/api/tests/test_policy.py`
- Operator rotation guide: `docs/operations/key-rotation-runbook.md`
- SQLite + vector compatibility checks: `docs/security/sqlite-encrypted-vector-compatibility.md`
- App-layer workspace isolation checks: `apps/api/tests/integration/test_app_authz_integration.py`

## Next Hardening Steps

1. Add signed audit exports and off-host retention policy.
2. Integrate session-based auth and CSRF protections for browser workflows.
3. Introduce KMS-backed envelope key support.
