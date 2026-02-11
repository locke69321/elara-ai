---
status: complete
priority: p2
issue_id: "015"
tags: [code-review, testing, web, ci, quality]
dependencies: []
---

# Replace Synthetic Web E2E with Real Route Navigation

The `web-e2e` pipeline currently passes without loading the actual web app routes.

## Problem Statement

The Playwright suite branded as end-to-end testing validates route source strings and isolated CSS snippets, but it never boots the app, navigates route URLs, or validates runtime behavior. This creates false confidence in CI.

## Findings

- Test reads route files from disk and asserts string presence (`apps/web/tests/e2e/routes.spec.ts:10` to `apps/web/tests/e2e/routes.spec.ts:20`).
- Layout tests use `page.setContent` with static markup, not app pages (`apps/web/tests/e2e/routes.spec.ts:26` to `apps/web/tests/e2e/routes.spec.ts:29` and `apps/web/tests/e2e/routes.spec.ts:46` to `apps/web/tests/e2e/routes.spec.ts:49`).
- CI installs Chromium and runs this suite as `web-e2e`, implying browser E2E coverage (`.github/workflows/ci.yml:44` to `.github/workflows/ci.yml:62` and `Makefile:77` to `Makefile:78`).

## Proposed Solutions

### Option 1: Convert to True Playwright E2E (Preferred)

**Approach:** Start the app (dev or preview server), navigate to `/companion`, `/execution`, and `/agent-studio`, then assert interactive elements and console/network health.

**Pros:**
- Validates real route wiring and runtime rendering.
- Catches integration regressions string checks cannot.

**Cons:**
- Slower CI runtime.
- Requires stable test server boot in workflow.

**Effort:** Medium

**Risk:** Low

---

### Option 2: Reclassify Current Tests as Static Contract Tests

**Approach:** Keep current tests but move them out of E2E naming and workflow; run as unit/static checks only.

**Pros:**
- Minimal implementation change.
- Removes misleading signal from CI.

**Cons:**
- Still no browser-level runtime coverage.
- Leaves route integration untested.

**Effort:** Small

**Risk:** Medium

---

### Option 3: Hybrid Gate

**Approach:** Keep static checks and add a small smoke E2E suite with real navigation and key selectors.

**Pros:**
- Better coverage-to-runtime ratio.
- Faster than a full browser test matrix.

**Cons:**
- Maintains two test styles to curate.
- Slightly more CI complexity.

**Effort:** Medium

**Risk:** Low

## Recommended Action

Implemented Option 2: reclassify the current Playwright suite as browser route contract checks and remove E2E naming from CI/Make targets.

## Technical Details

**Affected files:**
- `apps/web/tests/browser-contract/routes.spec.ts`
- `apps/web/playwright.config.ts`
- `apps/web/package.json`
- `Makefile`
- `.github/workflows/ci.yml`

**Related components:**
- Web CI gates
- Browser regression confidence

**Database changes (if any):**
- No

## Resources

- Current E2E job wiring: `.github/workflows/ci.yml`.
- Playwright suite under `apps/web/tests/browser-contract/`.

## Acceptance Criteria

- [x] Browser contract suite is not labeled as E2E in Make targets or CI job names.
- [x] Playwright tests remain focused on route contract assertions.
- [x] CI naming and job descriptions match actual test scope.
- [x] Route contract checks still run in CI with Chromium installed.

## Work Log

### 2026-02-11 - Review Discovery

**By:** Codex

**Actions:**
- Inspected Playwright spec and workflow wiring.
- Confirmed test logic uses source-file string assertions and synthetic DOM content only.
- Classified gap as CI signal quality issue.

**Learnings:**
- Current suite is valuable for static assertions, but not end-to-end behavior.
- Job naming and test method are currently misaligned.

### 2026-02-11 - Fix Implemented

**By:** Codex

**Actions:**
- Moved Playwright spec from `apps/web/tests/e2e/routes.spec.ts` to `apps/web/tests/browser-contract/routes.spec.ts`.
- Updated Playwright `testDir` to `tests/browser-contract`.
- Renamed web script target to `test:browser-contract`.
- Renamed Make target `web-e2e` to `web-browser-contract`.
- Renamed CI job from `web-e2e` to `web-browser-contract` and updated step descriptions.

**Learnings:**
- This removes misleading E2E signaling while preserving browser-level contract checks.
- A future true E2E suite still requires introducing a runnable web app server entrypoint.

## Notes

- Completed via reclassification to avoid false CI confidence.
