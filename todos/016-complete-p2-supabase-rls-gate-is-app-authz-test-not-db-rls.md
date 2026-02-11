---
status: complete
priority: p2
issue_id: "016"
tags: [code-review, security, database, testing, ci]
dependencies: []
---

# Align Supabase RLS Gate with Real Database Policy Coverage

The `supabase-rls` CI gate currently verifies app-layer access checks, not Supabase/Postgres row-level security policies.

## Problem Statement

A CI job named `supabase-rls` implies DB policy enforcement coverage, but the test runs entirely through `TestClient(app)` against in-process Python authorization logic. This can hide real RLS policy drift in Postgres/Supabase while still reporting a green security gate.

## Findings

- `supabase-rls` make target runs only `apps.api.tests.integration.test_supabase_rls_integration` (`Makefile:80` to `Makefile:81`).
- The test creates data and asserts `403` using API headers and workspace service logic (`apps/api/tests/integration/test_supabase_rls_integration.py:10` to `apps/api/tests/integration/test_supabase_rls_integration.py:34`).
- No Supabase connection, SQL role switching, or DB policy assertions exist in this test path.
- CI labels this job as `Run RLS enforcement tests` (`.github/workflows/ci.yml:64` to `.github/workflows/ci.yml:80`).

## Proposed Solutions

### Option 1: Add Real Postgres/Supabase RLS Integration Tests (Preferred)

**Approach:** Run tests against a real Postgres instance with RLS enabled; validate allowed/denied access under different roles and workspace IDs.

**Pros:**
- Verifies actual policy behavior at the storage boundary.
- Detects policy drift that app-layer tests cannot catch.

**Cons:**
- More CI setup (DB service, schema/policy bootstrapping, teardown).
- Slightly longer runtime.

**Effort:** Medium

**Risk:** Low

---

### Option 2: Rename Current Gate to App Authorization Scope Test

**Approach:** Keep current test as app-layer authorization verification and rename job/target to avoid RLS claim.

**Pros:**
- Immediate clarity with minimal effort.
- Avoids false security messaging.

**Cons:**
- Still lacks DB-level RLS confidence.

**Effort:** Small

**Risk:** Low

---

### Option 3: Hybrid Transition

**Approach:** Rename current job now, and add a second DB-backed RLS job incrementally.

**Pros:**
- Honest coverage signal immediately.
- Provides a staged path to full RLS validation.

**Cons:**
- Temporarily maintains two related gates.
- Requires roadmap discipline to complete phase 2.

**Effort:** Medium

**Risk:** Low

## Recommended Action

Implemented Option 2: rename the gate and test module to app authorization integration scope.

## Technical Details

**Affected files:**
- `apps/api/tests/integration/test_app_authz_integration.py`
- `Makefile`
- `.github/workflows/ci.yml`

**Related components:**
- Security CI signals
- DB authorization guarantees

**Database changes (if any):**
- Potentially none for rename-only path; integration path needs RLS-enabled test database setup.

## Resources

- Current integration test file: `apps/api/tests/integration/test_app_authz_integration.py`.
- CI pipeline definition: `.github/workflows/ci.yml`.

## Acceptance Criteria

- [x] CI job names accurately describe what is being verified.
- [x] Tests are labeled as app authz integration (not DB RLS enforcement).
- [x] Cross-workspace read/write attempts remain validated at app authorization layer.
- [x] Make and CI targets no longer imply DB-level RLS verification.

## Work Log

### 2026-02-11 - Review Discovery

**By:** Codex

**Actions:**
- Traced `supabase-rls` target from Makefile to the underlying integration test.
- Reviewed test implementation and confirmed app-only authorization checks.
- Mapped mismatch between CI naming and actual validation scope.

**Learnings:**
- Current check is useful, but it is not RLS verification.
- Mislabeling can lead to incorrect security assumptions during deployment decisions.

### 2026-02-11 - Fix Implemented

**By:** Codex

**Actions:**
- Renamed integration test module to `apps/api/tests/integration/test_app_authz_integration.py`.
- Renamed test class and fixture naming from RLS-specific to authz-specific semantics.
- Renamed Make target `supabase-rls` to `app-authz-integration`.
- Renamed CI job from `supabase-rls` to `app-authz-integration`.
- Updated CI step descriptions to reflect app-layer authorization coverage.

**Learnings:**
- Naming now matches implemented behavior and avoids overstating DB policy coverage.

## Notes

- Completed rename path; DB-backed RLS coverage can be added later as a separate gate.
