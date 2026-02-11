---
module: Authentication
date: 2026-02-10
problem_type: security_issue
component: authentication
symptoms:
  - "Audit event metadata stored raw invitation bearer tokens during invitation creation."
  - "Audit event metadata stored raw invitation bearer tokens during invitation acceptance."
  - "Owners querying /workspaces/{workspace_id}/audit-events could retrieve full invitation tokens."
root_cause: logic_error
resolution_type: code_fix
severity: high
tags: [invitation-token, audit-log, secret-redaction, fastapi]
---

# Troubleshooting: Raw Invitation Tokens Exposed In Audit Metadata

## Problem
Invitation bearer tokens were being written directly into audit event metadata for both invitation creation and invitation acceptance. Because audit events are readable via owner-facing endpoints and can be exported operationally, this expanded secret exposure risk.

## Environment
- Module: Authentication (Invitation workflow)
- Runtime: FastAPI Python API service (`apps/api`)
- Affected Component: Invitation create/accept audit logging
- Stage: Phase 2 API hardening
- Date solved: 2026-02-10

## Symptoms
- `invitation.created` metadata contained `token` with raw bearer token value.
- `invitation.accepted` metadata contained `token` with raw bearer token value.
- `/workspaces/{workspace_id}/audit-events` responses exposed those raw values to authorized owners.

## What Didn't Work

**Attempted Solution 1:** Keep logging raw token values for maximum traceability.
- **Why it failed:** Raw bearer credentials in logs violate secret-handling expectations and increase accidental leak surface.

**Attempted Solution 2:** Remove token metadata entirely.
- **Why it failed:** This removes correlation value between invitation creation and acceptance audit events.

## Solution
Replace raw token logging with a deterministic short fingerprint derived from SHA-256.

**Code changes**:
```python
# apps/api/main.py
from hashlib import sha256


def invitation_token_fingerprint(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()[:12]


# Before (invitation.created)
metadata={"email": payload.email, "token": invitation.token}

# After (invitation.created)
metadata={
    "email": payload.email,
    "token_fingerprint": invitation_token_fingerprint(invitation.token),
}

# Before (invitation.accepted)
metadata={"token": token, "role": membership.role}

# After (invitation.accepted)
metadata={
    "token_fingerprint": invitation_token_fingerprint(token),
    "role": membership.role,
}
```

**Verification tests added/updated**:
```python
# apps/api/tests/test_api_phase2.py
self.assertNotIn("token", created_event["metadata"])
self.assertNotIn("token", accepted_event["metadata"])
self.assertEqual(created_event["metadata"]["token_fingerprint"], expected_fingerprint)
self.assertEqual(accepted_event["metadata"]["token_fingerprint"], expected_fingerprint)

# apps/api/tests/e2e/test_dual_mode_flow.py
self.assertNotIn("token", created_event["metadata"])
self.assertNotIn("token", accepted_event["metadata"])
```

**Documentation update**:
- `docs/security/threat-model-v1.md` now explicitly states audit metadata stores invitation token fingerprints only.

## Why This Works
1. **Root cause:** Security-sensitive values were treated as normal audit metadata fields.
2. **Fix mechanism:** Fingerprinting preserves stable correlation while removing replayable bearer token material.
3. **Result:** Operational audit usefulness remains, while direct secret leakage through audit APIs/log exports is removed.

## Prevention
- Treat bearer credentials as secrets and never log raw values in audit metadata.
- Add regression tests whenever audit metadata shape changes for auth/invitation flows.
- Prefer deterministic, non-reversible identifiers (fingerprints) when event correlation is required.
- Keep threat model controls in sync with implementation and tests.

## Related Issues
No related issues documented yet.
