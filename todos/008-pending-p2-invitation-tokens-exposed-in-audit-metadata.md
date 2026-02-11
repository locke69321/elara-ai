---
status: complete
priority: p2
issue_id: "008"
tags: [code-review, security, audit, privacy]
dependencies: []
---

# Remove Raw Invitation Tokens From Audit Metadata

## Problem Statement

Invitation bearer tokens are written to audit metadata during creation and acceptance flows. Audit streams are often exported/shared for operations and compliance, so storing raw tokens increases accidental secret exposure risk.

## Findings

- Invitation creation logs `metadata={"email": payload.email, "token": invitation.token}` in `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:390`.
- Invitation acceptance logs `metadata={"token": token, "role": membership.role}` in `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:446`.
- Audit events are retrievable through `/workspaces/{workspace_id}/audit-events` for owners, increasing token visibility surface.

## Proposed Solutions

### Option 1: Redact Tokens In Audit Metadata

**Approach:** Replace token value with non-sensitive digest/prefix (or omit entirely) in audit events.

**Pros:**
- Fast, low-risk change.
- Keeps audit usefulness while removing secret leakage.

**Cons:**
- Requires updates to any tooling expecting full token in logs.

**Effort:** Small

**Risk:** Low

---

### Option 2: Store Token Fingerprint And Add Structured Secret-Handling Utility

**Approach:** Add helper utility for audit-safe metadata generation and enforce it for all bearer credentials.

**Pros:**
- Scales to other secret fields beyond invitation tokens.
- Makes secure logging policy explicit.

**Cons:**
- Slightly larger refactor.

**Effort:** Medium

**Risk:** Low

## Recommended Action

Implement Option 1 immediately with a deterministic token fingerprint in audit metadata
to preserve event correlation while removing raw bearer token exposure.

## Technical Details

**Affected files:**
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:390`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/main.py:446`
- `/Users/shawnconklin/Code/Projects/elara-ai/apps/api/tests/e2e/test_dual_mode_flow.py`

**Related components:**
- Immutable audit log ingestion and event export endpoint
- Invitation lifecycle endpoints

**Database changes (if any):**
- Migration needed? No
- New columns/tables? None

## Resources

- **Review target:** current branch `codex/phase2-dual-mode-core`

## Acceptance Criteria

- [x] Audit events no longer contain raw invitation tokens.
- [x] Equivalent observability is preserved with redacted identifiers/fingerprints.
- [x] Tests assert token redaction behavior for create and accept flows.
- [x] Security documentation reflects secret-logging policy.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Reviewed invitation and audit endpoint flows.
- Identified direct bearer token logging at creation and acceptance points.
- Drafted immediate and scalable remediation options.

**Learnings:**
- Audit fidelity and secret hygiene need explicit balancing rules to avoid leakage through observability channels.

### 2026-02-11 - Invitation Token Audit Redaction Complete

**By:** Codex

**Actions:**
- Added failing API and e2e tests asserting invitation audit metadata excludes raw `token` and includes `token_fingerprint`.
- Implemented deterministic invitation token fingerprinting (`sha256` prefix) in API audit logging for both invitation creation and acceptance events.
- Replaced raw token fields in audit metadata with `token_fingerprint`, preserving correlation value without secret disclosure.
- Updated threat model documentation to explicitly state invitation bearer tokens are redacted in audit logs.
- Verified full repository quality gates with `make check` (coverage 96%).

**Learnings:**
- Short deterministic fingerprints preserve operational traceability while materially reducing accidental secret exposure through audit exports.
