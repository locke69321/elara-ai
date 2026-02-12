---
status: complete
priority: p1
issue_id: "011"
tags: [code-review, security, authorization, api]
dependencies: []
---

# Deny Replay Access When ACL Record Is Missing

## Problem Statement

Event replay currently allows access when a run has no `run_access_record` row. This creates an authorization bypass for any legacy or partially-migrated run data and can expose run timelines to unauthorized actors.

## Findings

- In `apps/api/agents/runtime.py:341`, replay authorization checks `is_run_access_allowed(...)` and only rejects on explicit `False`.
- In `apps/api/events/outbox.py:209`, `is_run_access_allowed` returns `None` when no ACL rows exist for a run.
- Combined behavior means `None` is treated as allow, not deny.
- Repro (local): seed `run_event_record` without `run_access_record`, then call `runtime.replay_events(...)` as an unrelated actor; replay succeeds.

## Proposed Solutions

### Option 1: Deny by Default on Missing ACL

**Approach:** Treat `None` from `is_run_access_allowed` as unauthorized and raise `PermissionError`.

**Pros:**
- Closes bypass immediately.
- Smallest code change.

**Cons:**
- Legacy runs without ACL rows become inaccessible until migrated.

**Effort:** Small

**Risk:** Low

---

### Option 2: Deny by Default + One-Time Backfill

**Approach:** Implement Option 1 and add a migration/backfill that derives run ACL rows from known ownership data before rollout.

**Pros:**
- Preserves access to historical runs.
- Strongest production rollout path.

**Cons:**
- Requires migration planning and validation.

**Effort:** Medium

**Risk:** Medium

---

### Option 3: Signed Replay Tokens

**Approach:** Require short-lived signed replay tokens issued at run creation or execution completion.

**Pros:**
- Strong explicit authorization model.
- Reduces reliance on mutable ACL tables.

**Cons:**
- Larger API/client change.
- More operational complexity.

**Effort:** Large

**Risk:** Medium

## Recommended Action

Implemented Option 1 (deny-by-default on missing ACL) and added regression coverage across e2e/integration/unit replay paths.

## Technical Details

**Affected files:**
- `apps/api/agents/runtime.py:341`
- `apps/api/events/outbox.py:179`

**Related components:**
- Event replay API: `apps/api/main.py:419`
- Outbox persistence tables in `apps/api/db/state.py:62`

**Database changes (if any):**
- Optional backfill for `run_access_record`.

## Resources

- **Review target:** Working tree on `codex/phase5-gap-closure`
- **Related artifact:** `apps/api/tests/integration/test_runtime_integration.py`

## Acceptance Criteria

- [x] Replay requests are denied when ACL data is missing.
- [x] Existing authorized replay paths still pass.
- [x] Regression test covers legacy run rows without access records.
- [x] Security review confirms no bypass remains.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Reviewed replay authorization path in runtime and outbox layers.
- Reproduced unauthorized replay using a seeded run with no ACL row.
- Documented mitigation options and rollout tradeoffs.

**Learnings:**
- Current logic treats "unknown authorization" as allow.
- Deny-by-default is required for secure replay semantics.

### 2026-02-11 - Remediation Completed

**By:** Codex

**Actions:**
- Updated runtime replay authorization to reject when persisted ACL state is missing (`None`) instead of allowing by default.
- Added e2e regression test for legacy runs with `run_event_record` rows and no `run_access_record`.
- Added integration and unit tests that assert missing ACL rows are denied.
- Ran `make check` to validate lint, typecheck, and coverage gates.

## Notes

- This is a merge-blocking finding because it impacts authorization guarantees.
