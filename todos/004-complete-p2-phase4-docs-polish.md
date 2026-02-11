---
status: complete
priority: p2
issue_id: "004"
tags: [phase4, docs, setup, ops, user-guide]
dependencies: ["001", "002", "003"]
---

# Phase 4 V1 Docs and Operator Guidance

Deliver the Phase 4 documentation set for setup, user guidance, and backup/restore operations.

## Problem Statement

Core functionality exists through phase 3, but operator and user-facing documentation is incomplete. New users and self-host operators need clear, practical instructions for setup, day-one usage, and data protection workflows.

## Findings

- Existing docs cover architecture and security threat modeling.
- Required Phase 4 docs (`setup`, `agent-studio`, `memory-controls`, `backup-restore`) are missing.
- The current stack supports uv/pnpm local setup and docker-compose baseline for API containerization.

## Proposed Solutions

### Option 1: Practical docs aligned to current implementation (selected)

Write four docs with copy-paste commands and realistic examples that match the current codebase and API surface.

Pros:
- Immediately useful for local users and operators
- Avoids speculative guidance for unimplemented features

Cons:
- Some flows remain API-first due frontend scaffold status

Effort: 2-4 hours
Risk: Low

## Recommended Action

Create the four Phase 4 docs, include explicit prerequisites and troubleshooting notes, and update the plan/todo to reflect completion.

## Technical Details

Paths to create:
- `docs/setup/self-hosted-quickstart.md`
- `docs/user-guide/agent-studio.md`
- `docs/user-guide/memory-controls.md`
- `docs/ops/backup-restore.md`

## Acceptance Criteria

- [x] Self-host quickstart guide exists with local and docker-compose setup steps.
- [x] Agent Studio user guide explains specialist creation and capability boundaries.
- [x] Memory controls guide explains memory behavior, review, and redaction guidance.
- [x] Backup/restore runbook covers SQLite and PostgreSQL variants.
- [x] Documentation references current API surface and security controls.
- [x] Plan progress updated for Phase 4 deliverables.

## Work Log

### 2026-02-11 - Todo Created

**By:** Codex

**Actions:**
- Created Phase 4 docs todo linked to completed phases 1-3.
- Scoped deliverables to the exact Phase 4 plan outputs.

**Learnings:**
- API-first examples are necessary while frontend runtime remains scaffold-level.

### 2026-02-11 - Phase 4 Docs Delivered

**By:** Codex

**Actions:**
- Added setup guide: `docs/setup/self-hosted-quickstart.md`.
- Added user guides:
  - `docs/user-guide/agent-studio.md`
  - `docs/user-guide/memory-controls.md`
- Added operator runbook: `docs/ops/backup-restore.md`.
- Updated plan execution progress for Phase 4.

**Learnings:**
- Current project state is best documented with API-first flows and explicit notes where UI/runtime persistence are still scaffold-level.
