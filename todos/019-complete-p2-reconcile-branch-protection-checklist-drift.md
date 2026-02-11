---
status: complete
priority: p2
issue_id: "019"
tags: [code-review, planning, quality, release]
dependencies: []
---

# Reconcile Branch Protection Checklist Drift

## Problem Statement

Branch-protection and release-readiness status is inconsistent across the two most recent plans. Conflicting checkbox states can cause incorrect release decisions and unclear operator responsibilities.

## Findings

- `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md:167` marks branch-protection configuration as complete.
- `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md:202` marks branch-protection acceptance as complete.
- `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md:211` still lists branch-protection configuration as incomplete.
- `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md:256` still lists enforcement status as incomplete.
- `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md:259` still lists applying branch protection in UI as a remaining external action.

## Proposed Solutions

### Option 1: Live-System Verification + Atomic Plan Update

**Approach:** Verify current GitHub branch-protection settings once, then update both plans in the same commit with a dated verification note and identical status.

**Pros:**
- Fastest path to consistent truth.
- Reduces release-readiness ambiguity immediately.

**Cons:**
- Requires repo admin visibility to verify accurately.

**Effort:** 30-60 minutes

**Risk:** Low

---

### Option 2: Single Owner Checklist for External Admin Actions

**Approach:** Move all branch-protection UI actions to one checklist section in one file and reference it from other plans.

**Pros:**
- Prevents future checkbox divergence.
- Clarifies operational ownership.

**Cons:**
- Requires minor structural updates in both files.

**Effort:** 1 hour

**Risk:** Low

---

### Option 3: Add Evidence Artifact Gate

**Approach:** Require a committed evidence artifact (screenshot/log snippet/date stamp) for branch-protection completion before checking related plan boxes.

**Pros:**
- Auditable and repeatable.
- Helps future reviews.

**Cons:**
- Slightly more process overhead.

**Effort:** 1-2 hours

**Risk:** Medium

## Recommended Action

Completed via canonical-owner reconciliation plus live verification: keep branch-protection execution state in one active plan, verify GitHub branch-protection settings via API, and remove branch-protection drift from secondary/superseded planning artifacts.

## Technical Details

**Affected files:**
- `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md`
- `docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md`
- `docs/security/branch-protection-main.md`

**Related components:**
- GitHub branch protection controls for `main`
- CI required-check gate enforcement

## Resources

- Review target notes from `2026-02-11` workflows-review pass
- `docs/security/branch-protection-main.md`
- GitHub repository branch protection settings for `main`

## Acceptance Criteria

- [x] Branch-protection status is identical across both plans where they reference the same gate.
- [x] A dated verification note identifies who verified the live GitHub settings and when.
- [x] No "remaining external action" remains for branch protection if acceptance is checked complete.
- [x] CI-required checks listed in planning docs match repository settings.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Compared branch-protection and release-gate checklist items between the two newest plans.
- Recorded specific contradictory checkbox states with line references.
- Prepared resolution options focused on one-source status governance.

**Learnings:**
- Checklist drift already exists across plan boundaries for external admin tasks.
- Plan-state consistency requires either one owner checklist or atomically synchronized updates.

### 2026-02-11 - Resolution

**By:** Codex

**Actions:**
- Queried live branch protection with `gh api repos/locke69321/elara-ai/branches/main/protection`.
- Confirmed required checks include:
  - `ci / check`
  - `ci / coverage-all`
  - `ci / web-browser-contract`
  - `ci / app-authz-integration`
  - `ci / sqlite-compat`
  - `ci / semantic-pr-title`
  - `ci / commitlint`
  - `ci / branch-name`
- Updated canonical plan to include a dated branch-protection verification snapshot and reconciled related checkboxes.
- Removed branch-protection drift from active planning by converting the secondary plan to superseded reference-only content.

**Learnings:**
- Keeping a single authoritative checklist plus an evidence note prevents future status contradictions.
