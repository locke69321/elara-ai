---
status: complete
priority: p2
issue_id: "018"
tags: [code-review, planning, architecture, release]
dependencies: []
---

# Consolidate v0.1 Plan Ownership

## Problem Statement

Two same-day v0.1 plans split tightly coupled work that is being executed as one stream. This creates duplicate tracking, hidden dependencies, and no single authoritative definition of "done" for v0.1 closure.

## Findings

- `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md:36` states this is the remaining v0.1 closure plan and keeps execution to one phase.
- `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md:19` declares it must be completed before the gap-closure plan can be closed.
- `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md:128` introduces a full multi-phase plan for work that materially affects v0.1 release readiness and overlaps the gap-closure release-gate stream.
- `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md:196` already has a release-gate workstream, but the release-governance plan tracks much of the same readiness surface separately.

## Proposed Solutions

### Option 1: Merge Into One Canonical Plan

**Approach:** Fold release-governance phases into the gap-closure plan as explicit workstreams and keep one checklist hierarchy.

**Pros:**
- Single source of truth for v0.1 readiness.
- Eliminates cross-plan dependency ambiguity.

**Cons:**
- Requires a one-time restructure/edit pass.

**Effort:** 1-2 hours

**Risk:** Low

---

### Option 2: Keep Two Docs, Convert One to Reference Spec

**Approach:** Keep gap-closure as executable plan and convert release-governance doc to ADR/spec with no execution checkboxes.

**Pros:**
- Preserves context without losing detail.
- Prevents dual tracking.

**Cons:**
- Two files still exist and need clear ownership language.

**Effort:** 1 hour

**Risk:** Low

---

### Option 3: Keep Split Plans With Explicit Sync Contract

**Approach:** Retain both plans, but add a mandatory sync block mapping every shared acceptance criterion to one owner plan.

**Pros:**
- Minimal structural change.
- Can be applied quickly.

**Cons:**
- Ongoing maintenance overhead.
- Drift risk remains higher than Option 1/2.

**Effort:** 1 hour initial + ongoing upkeep

**Risk:** Medium

## Recommended Action

Completed using Option 1 (single canonical execution plan): merged release-governance execution tracking into the gap-closure plan and marked the secondary plan as superseded/non-executable.

## Technical Details

**Affected files:**
- `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md`
- `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md`

**Related components:**
- v0.1 release gating and branch protection readiness workflow
- CI/automation governance tracking

## Resources

- Review target notes from `2026-02-11` workflows-review pass
- `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md`
- `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md`

## Acceptance Criteria

- [x] Exactly one canonical plan is marked as execution authority for v0.1 closure.
- [x] Any secondary document is explicitly non-executable or fully scoped to non-overlapping work.
- [x] Cross-plan dependencies are removed or replaced with a single ownership mapping table.
- [x] "Done" criteria for v0.1 can be evaluated from one checklist without cross-referencing another execution plan.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Reviewed the two most recent same-date v0.1 plans for scope boundaries and execution ownership.
- Identified split ownership across release readiness and release governance workstreams.
- Documented consolidation options with tradeoffs.

**Learnings:**
- The release-governance plan functions as an execution dependency of the gap-closure plan, not a cleanly independent stream.
- Plan execution would be easier to reason about with one canonical owner document.

### 2026-02-11 - Resolution

**By:** Codex

**Actions:**
- Marked `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md` as canonical for v0.1 closure with merged-source metadata.
- Added merged release/governance workstream and appended requested branch-governance addendum in the canonical plan.
- Marked `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md` as superseded/non-executable.

**Learnings:**
- One owner checklist removes plan-state drift and simplifies release readiness tracking.
