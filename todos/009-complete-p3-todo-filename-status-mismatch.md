---
status: complete
priority: p3
issue_id: "009"
tags: [code-review, quality, process, automation]
dependencies: []
---

# Align Todo Filename Status With Frontmatter

## Problem Statement

Multiple todo files use a `pending` status in the filename while YAML frontmatter marks them `complete`. This breaks the contract expected by file-based triage tooling and makes pending-work queries inaccurate.

## Findings

- `todos/005-pending-p1-auth-header-defaults-allow-owner-bypass.md` has `status: complete`.
- `todos/006-pending-p1-event-replay-leaks-cross-workspace-data.md` has `status: complete`.
- `todos/007-pending-p1-approval-decision-not-scoped-to-workspace.md` has `status: complete`.
- `todos/008-pending-p2-invitation-tokens-exposed-in-audit-metadata.md` has `status: complete`.
- Filename status token is `pending` for all four files, conflicting with frontmatter status.
- The `file-todos` workflow and helper commands rely on consistent filename + frontmatter status.

## Proposed Solutions

### Option 1: Rename The File To `complete`

**Approach:** Rename issues `005` to `008` from `...-pending-...` to `...-complete-...` and keep frontmatter as-is.

**Pros:**
- Preserves completed state already recorded in the document.
- Restores status consistency with minimal change.

**Cons:**
- Requires updating any references that point to the old filename.

**Effort:** Small

**Risk:** Low

---

### Option 2: Change Frontmatter Back To `pending`

**Approach:** Keep filename unchanged and set `status: pending`.

**Pros:**
- No rename needed.
- Keeps current file path stable.

**Cons:**
- Reopens a task that appears already completed in work log and acceptance criteria.
- Can create process confusion during triage.

**Effort:** Small

**Risk:** Medium

---

### Option 3: Add A Consistency Guard

**Approach:** Add a lint/check script that enforces filename status token equals frontmatter status for all todos.

**Pros:**
- Prevents recurrence.
- Improves automation reliability.

**Cons:**
- Additional maintenance surface.
- More work than immediate fix.

**Effort:** Medium

**Risk:** Low

## Recommended Action

Renamed issues `005` through `008` to `*-complete-*` to align file status with frontmatter, then verified no remaining mismatches in the todo set.

## Technical Details

**Affected files:**
- `/Users/shawnconklin/Code/Projects/elara-ai/todos/005-complete-p1-auth-header-defaults-allow-owner-bypass.md`
- `/Users/shawnconklin/Code/Projects/elara-ai/todos/006-complete-p1-event-replay-leaks-cross-workspace-data.md`
- `/Users/shawnconklin/Code/Projects/elara-ai/todos/007-complete-p1-approval-decision-not-scoped-to-workspace.md`
- `/Users/shawnconklin/Code/Projects/elara-ai/todos/008-complete-p2-invitation-tokens-exposed-in-audit-metadata.md`

**Related components:**
- File-based todo triage workflow
- Todo status listing commands based on filename globbing

**Database changes (if any):**
- Migration needed? No
- New columns/tables? None

## Resources

- **Review target:** current branch `codex/phase2-dual-mode-core` (latest diff `HEAD~1..HEAD`)
- **Skill reference:** `/Users/shawnconklin/.codex/skills/file-todos/SKILL.md`

## Acceptance Criteria

- [x] Issues `005` through `008` have consistent filename and frontmatter statuses.
- [x] `ls todos/*-pending-*.md` does not include completed items.
- [x] Team workflow documentation assumptions remain valid.

## Work Log

### 2026-02-11 - Initial Discovery

**By:** Codex

**Actions:**
- Reviewed todo status consistency and detected filename/frontmatter mismatch for issues `005` through `008`.
- Assessed impact on pending todo triage commands and automation assumptions.
- Documented remediation options and triage-ready acceptance criteria.

**Learnings:**
- File-based workflows are sensitive to status drift between filename metadata and document metadata.

### 2026-02-11 - Resolution

**By:** Codex

**Actions:**
- Renamed completed todo files to match frontmatter:
  - `005-pending-p1-auth-header-defaults-allow-owner-bypass.md` -> `005-complete-p1-auth-header-defaults-allow-owner-bypass.md`
  - `006-pending-p1-event-replay-leaks-cross-workspace-data.md` -> `006-complete-p1-event-replay-leaks-cross-workspace-data.md`
  - `007-pending-p1-approval-decision-not-scoped-to-workspace.md` -> `007-complete-p1-approval-decision-not-scoped-to-workspace.md`
  - `008-pending-p2-invitation-tokens-exposed-in-audit-metadata.md` -> `008-complete-p2-invitation-tokens-exposed-in-audit-metadata.md`
- Verified todo filename/frontmatter status consistency with a directory-wide check.

**Learnings:**
- Status consistency should be validated automatically to prevent triage/reporting drift.
