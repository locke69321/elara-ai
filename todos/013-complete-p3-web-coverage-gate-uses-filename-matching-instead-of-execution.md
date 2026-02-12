---
status: complete
priority: p3
issue_id: "013"
tags: [code-review, quality, testing, web]
dependencies: []
---

# Replace Filename-Match Coverage Gate with Executed Coverage

## Problem Statement

The web coverage gate reports coverage by checking whether test source files contain route/style filenames, not whether application code was actually executed. This can report 100% even when runtime behavior is untested.

## Findings

- `apps/web/scripts/coverage_gate.mjs:24` computes coverage via `allTestContent.includes(fileName)`.
- The resulting percent is based on filename presence, not instrumentation.
- This weakens confidence in `make coverage-all`, because web coverage can pass without exercising code paths.

## Proposed Solutions

### Option 1: Switch to Instrumented Coverage (Preferred)

**Approach:** Use a real coverage tool for Node/TS tests (for example `c8` or V8 coverage integration) and enforce a threshold on executed lines/branches.

**Pros:**
- Accurate signal.
- Aligns with backend coverage gate semantics.

**Cons:**
- Setup and configuration effort.

**Effort:** Medium

**Risk:** Low

---

### Option 2: Keep Current Script but Rename It

**Approach:** Rename script/target to "traceability gate" and stop calling it coverage.

**Pros:**
- Very low effort.
- Removes misleading terminology.

**Cons:**
- Still does not provide real execution coverage.

**Effort:** Small

**Risk:** Medium

---

### Option 3: Add Lightweight Runtime Smoke Coverage

**Approach:** Keep static gate but add mandatory executed smoke suite over key routes/components.

**Pros:**
- Incremental improvement without full tooling migration.

**Cons:**
- Partial signal; still not full coverage.

**Effort:** Small/Medium

**Risk:** Medium

## Recommended Action

Implemented Option 1 with an execution-driven coverage gate backed by Node test coverage plus executed-route verification.

## Technical Details

**Affected files:**
- `apps/web/scripts/coverage_gate.mjs:24`
- `apps/web/package.json:11`
- `Makefile:62`

**Related components:**
- CI workflow coverage jobs in `.github/workflows/ci.yml`

**Database changes (if any):**
- None.

## Resources

- **Review target:** Working tree on `codex/phase5-gap-closure`
- **Related tests:** `apps/web/tests/structure.test.mjs`, `apps/web/tests/route-states.test.mjs`

## Acceptance Criteria

- [x] Web coverage gate measures executed code, not filename references.
- [x] Coverage threshold remains enforced in CI.
- [x] `make coverage-all` fails when key route code is unexecuted.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Reviewed web coverage gate implementation and npm scripts.
- Confirmed metric is based on file-name text matching.
- Documented remediation options with tradeoffs.

**Learnings:**
- Current gate is useful for traceability but not coverage assurance.
- Naming and enforcement semantics should match measured behavior.

### 2026-02-11 - Remediation Completed

**By:** Codex

**Actions:**
- Replaced filename-text matching logic in `apps/web/scripts/coverage_gate.mjs` with an execution-based gate:
  - runs Node tests with coverage enabled;
  - validates executed route modules against required route files;
  - enforces threshold and writes `coverage/web-coverage.json`.
- Added `apps/web/tests/executed-routes.test.mjs` to execute route modules via transpile+VM stubs and emit executed-file signals.
- Added `apps/web/tests/coverage-gate.test.mjs` to verify the gate fails when route execution coverage is missing and passes when present.
- Updated web package scripts so `pnpm --filter elara-web coverage` runs the new coverage gate.
- Ran `make check` to validate lint, typecheck, and coverage gates.

## Notes

- This is not merge-blocking by itself, but it reduces test signal quality.
