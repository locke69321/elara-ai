---
title: "feat: Dual-Mode v0.1 Remaining Gap Closure"
type: feat
date: 2026-02-11
source_brainstorm: docs/brainstorms/2026-02-10-agent-native-companion-platform-brainstorm.md
source_plan: docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md
merged_from:
  - docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md
canonical_for_v0_1_closure: true
scope: single-phase
deepened_on: 2026-02-11
research_inputs:
  - frontend-design
  - deepen-plan
  - docs/solutions/security-issues/raw-invitation-tokens-in-audit-metadata-authentication-20260210.md
  - docs/solutions/security-issues/cross-workspace-leakage-and-member-high-impact-delegation-authorization-20260211.md
---

# feat: Dual-Mode v0.1 Remaining Gap Closure

## Enhancement Summary

**Deepened on:** 2026-02-11  
**Scope model:** Single phase, multi-workstream execution  
**Sections enhanced:** 9

### Key Improvements
1. Added a concrete production UI direction (visual system, interaction model, route-level behavior) instead of placeholder shell language.
2. Added one-phase execution workstreams with explicit file-level deliverables and outside-in test sequencing.
3. Added measurable completion gates for durability, security, performance, RLS enforcement, and encrypted-vector compatibility.

### New Considerations Discovered
- Current route files are mostly static and need real server-function/API integration before they satisfy dual-mode product intent.
- Current invitation/approval/audit and memory layers are in-memory scaffolding, so restart durability is the largest v0.1 readiness gap.
- Prior security learnings must be preserved during persistence refactors to avoid regression in token secrecy and workspace isolation.

## Overview

This plan closes only the missing v0.1 implementation work left after the original dual-mode plan, and keeps execution to one phase.
It is the single canonical execution plan for v0.1 closure, including the release/versioning governance items that were previously tracked in a separate plan.

Context used:
- Brainstorm (WHAT to build): `docs/brainstorms/2026-02-10-agent-native-companion-platform-brainstorm.md`
- Original plan (baseline + unchecked criteria): `docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md`
- Institutional learnings:
  - `docs/solutions/security-issues/raw-invitation-tokens-in-audit-metadata-authentication-20260210.md`
  - `docs/solutions/security-issues/cross-workspace-leakage-and-member-high-impact-delegation-authorization-20260211.md`

## Problem Statement / Motivation

The prior plan documents significant progress, but v0.1 is not release-ready because the largest remaining items are still scaffold-level:
- Memory adapters are stubs (`apps/api/memory/store_sqlite.py`, `apps/api/memory/store_postgres.py`).
- Invitations, approvals, and audit logs are in-memory services (`apps/api/auth/invitations.py`, `apps/api/safety/approvals.py`, `apps/api/audit/logging.py`).
- Web routes are static shells without full product behavior (`apps/web/src/routes/companion.tsx`, `apps/web/src/routes/execution.tsx`, `apps/web/src/routes/agent-studio.tsx`).
- Security/performance/compatibility gates still have open checklist items (`docs/security/threat-model-v1.md`).

## Proposed Solution

Deliver a single integrated gap-closure phase that ships:
1. Durable persistence for memory, invitation, approval, and audit domains.
2. A proper dual-mode UI with real workflow integration, mobile-safe behavior, and clear visual identity.
3. Verified release gates for performance, Supabase RLS security, and SQLite encrypted-vector compatibility.

## Product UI Direction (Frontend Skill Applied)

### Aesthetic Direction

Adopt a **"Field Console (Night Shift)"** visual language: editorial typography + operational telemetry in a dark cockpit atmosphere. The UI should feel like a companion notebook fused with a mission-control surface, not a generic dashboard.

### Visual System

- Typography:
  - Display: `Fraunces` (headings, section identities)
  - Body/UI: `Public Sans` (forms, controls, reading comfort)
  - Monospace: `IBM Plex Mono` (event IDs, sequence numbers, diagnostics)
- Color tokens (dark-first, high contrast):
  - Background: charcoal-black gradient (`#0B0F14` -> `#121922`)
  - Surface: graphite panels with subtle steel borders (`#161D27`, `#2A3442`)
  - Primary accent: electric teal (`#22D3EE`)
  - Secondary accent: indigo-cyan blend for focus/selection
  - Warning/approval state: amber (`#F59E0B`)
  - High-impact state: ember red (`#EF4444`)
- Motion:
  - Staggered page-load reveal for mode panels
  - Timeline rows animate by event type
  - Approval-required state uses a visible interruption pattern, not silent toast-only feedback
- Composition:
  - Asymmetric two-column layout on desktop
  - Stacked single-column flow on mobile
  - Persistent mode switch and workspace context at top

### Route-Level UX Deliverables

- `apps/web/src/routes/companion.tsx`
  - Real message composer, response list, and memory-hit transparency chips.
- `apps/web/src/routes/execution.tsx`
  - Goal submission, delegated result cards, replay controls (`last_seq` resume), approval-required interruption panel.
- `apps/web/src/routes/agent-studio.tsx`
  - Specialist list + create/edit form with capability toggles and owner/member constraints surfaced in UI.
- `apps/web/src/routes/__root.tsx`
  - Shared shell with mode switch, workspace identity, status badge for runtime/connection.

### Frontend Architecture Notes

- Introduce route-safe server boundary functions in `apps/web/src/lib/server/` for privileged API operations.
- Add reusable UI primitives in `apps/web/src/components/`:
  - `app-shell.tsx`, `mode-tabs.tsx`, `timeline-event.tsx`, `approval-banner.tsx`, `specialist-form.tsx`, `memory-hit-chip.tsx`.
- Add `apps/web/src/styles/tokens.css` for design tokens and typography setup.

## Technical Approach

### API + Persistence Workstream

- Replace in-memory stores with durable repository-backed services:
  - Invitations: `apps/api/auth/invitations.py`
  - Approvals: `apps/api/safety/approvals.py`
  - Audit events: `apps/api/audit/logging.py`
  - Agent run events/outbox replay source: `apps/api/events/outbox.py`
- Add/update migrations under `apps/api/db/migrations/` for:
  - invitation records, membership bindings
  - approval requests/decisions
  - audit events with immutable hash-chain fields
  - persistent `agent_run_event` and `agent_run_event_outbox` replay/outbox records
  - memory item + embedding persistence alignment
- Keep startup wiring centralized in `apps/api/main.py` lifespan composition.

### Memory Backend Parity Workstream

- Implement real adapter behavior in:
  - `apps/api/memory/store_sqlite.py`
  - `apps/api/memory/store_postgres.py`
- Enforce shared retrieval contract:
  - workspace + agent scoping
  - deterministic top-k ordering
  - explicit embedding-model metadata and dimension guardrails
- Add adapter conformance tests to compare behavior parity and leakage prevention.

### Security Preservation Workstream

- Preserve and re-assert prior learnings:
  - Never log raw invitation token in audit metadata.
  - Maintain strict workspace boundary checks on all workspace-scoped routes.
  - Keep member high-impact delegation denial behavior intact.
- Complete remaining checklist items in `docs/security/threat-model-v1.md`:
  - tool allowlist enforcement documented and tested
  - key rotation runbook finalized with rollback steps

### Performance + Compatibility Workstream

- Add benchmark harness in `scripts/perf/`:
  - `scripts/perf/run_api_latency.py`
  - `scripts/perf/run_memory_retrieval.py`
  - `scripts/perf/fixtures/generate_fixture_dataset.py`
- Add CI/local hooks in `Makefile` for reproducible runs.
- Add app-layer workspace authz integration tests in `apps/api/tests/integration/test_app_authz_integration.py`.
- Add compatibility evidence doc and CI checks for SQLCipher + vector runtime in `docs/security/sqlite-encrypted-vector-compatibility.md`.
- Treat Supabase RLS CI checks as mandatory merge gates (no bypass for PRs touching API/data access code).

### GitHub CI + Branch Protection Workstream

- Add GitHub Actions workflow(s) under `.github/workflows/` to run required gates on pull requests targeting `main`.
- Define required status checks for merge:
  - `ci / check` (`make check`)
  - `ci / coverage-all` (`make coverage-all`, includes API + web + worker)
  - `ci / web-browser-contract` (`make web-browser-contract`)
  - `ci / app-authz-integration` (app authz integration suite)
  - `ci / sqlite-compat` (SQLCipher + vector compatibility verification)
- Configure branch protection on `main` as final merge control:
  - Require pull request before merge
  - Require all required status checks to pass
  - Require branch to be up to date before merge
  - Dismiss stale approvals when new commits are pushed
  - Do not allow direct pushes to `main`
- Treat branch protection as blocking release gate: no merge to `main` unless all required CI checks are green.

## Implementation Plan (Single Phase)

### Phase 5: v0.1 Gap Closure (One Phase)

#### Workstream A: Durable Domain Persistence
- [x] Add failing e2e tests for restart persistence of invitations, approvals, audit events, and run-event replay in `apps/api/tests/e2e/test_dual_mode_flow.py`.
- [x] Add failing integration tests for repository-backed service behavior in `apps/api/tests/integration/test_runtime_integration.py`.
- [x] Add failing unit tests for service edge cases in `apps/api/tests/unit/test_invitations_unit.py`, `apps/api/tests/unit/test_approvals_unit.py`, `apps/api/tests/unit/test_audit_unit.py`.
- [x] Add failing unit/integration tests for durable outbox sequencing and replay cursor behavior in `apps/api/tests/test_outbox.py` and `apps/api/tests/integration/test_runtime_integration.py`.
- [x] Implement repositories/services and migration updates, including persistent outbox + replay storage in `apps/api/events/outbox.py`.

#### Workstream B: Memory Adapter Completion
- [x] Add failing e2e tests for cross-backend memory retrieval parity and isolation.
- [x] Add failing integration tests for SQLite/Postgres adapter conformance.
- [x] Add failing unit tests for ordering, scoping, and dimension mismatch handling.
- [x] Implement adapter persistence and retrieval logic.

#### Workstream C: Proper UI Delivery
- [x] Add Playwright browser e2e harness (`apps/web/playwright.config.ts`) and failing tests for companion messaging, execution workflow, and specialist management in `apps/web/tests/e2e/`.
- [x] Add route-level integration tests for approval-required and replay resume UI states.
- [x] Implement componentized UI, tokenized styling, and server-function data boundaries.
- [x] Ensure mobile and desktop usability with explicit responsive test assertions.
- [x] Add CI target (`make web-browser-contract`) and run browser route contract checks in CI as a required check.

#### Workstream D: Release Gate Completion
- [x] Add benchmark scripts + fixture generation and wire `make perf` target.
- [x] Replace API-only coverage with full-repo coverage commands in `Makefile`:
  - `make api-coverage`
  - `make web-coverage`
  - `make worker-coverage`
  - `make coverage-all` (aggregates all three)
- [x] Enforce minimum coverage thresholds per surface in CI (API >= 90%, web >= 90%, worker >= 90%).
- [x] Ensure worker test suite exists and is included in `make worker-coverage`.
- [x] Ensure frontend coverage report generation is included in `make web-coverage`.
- [x] Add Supabase RLS enforcement tests and negative cross-workspace tests.
- [x] Configure Supabase RLS test job as mandatory/required PR status check.
- [x] Add SQLite encrypted-vector compatibility matrix document + CI validation step.
- [x] Close remaining threat-model checklist items with implementation evidence.
- [x] Add GitHub Actions CI workflow file(s) in `.github/workflows/ci.yml` (or split workflows) for required checks on PRs to `main`.
- [x] Configure GitHub branch protection for `main` with required checks and no direct pushes.
- [x] Verify merge is blocked when any required check fails, and allowed only when all required checks pass.

#### Workstream E: Release Process + Branch Governance (Merged)
- [x] Re-baseline release semantics to pre-1.0 (`v0.0.1` initial publish, active `v0.1.x` stream) and align docs.
- [x] Add release automation files:
  - `.github/workflows/release-please.yml`
  - `release-please-config.json`
  - `.release-please-manifest.json`
- [x] Add naming/governance enforcement:
  - `.github/workflows/semantic-pr-title.yml`
  - `.github/workflows/commitlint.yml`
  - `.github/workflows/branch-name.yml`
  - `commitlint.config.cjs`
  - `scripts/ci/validate-branch-name.sh`
- [x] Add contributor guidance in `AGENTS.md` and `.github/pull_request_template.md`.
- [x] Update branch protection guidance in `docs/security/branch-protection-main.md` with release/governance checks.
- [ ] Verify release-please creates/updates release PRs on `main` and updates changelog entries as expected.
- [ ] Validate governance failure/success modes in live PRs:
  - invalid branch names block merge
  - invalid PR titles block merge
  - non-conventional commit messages block merge
  - compliant PRs merge and feed release-please correctly
- [x] Confirm repository setting "Default to PR title for squash merge commits" is enabled.

## SpecFlow Coverage (Updated)

### Core Flows
1. Owner sends companion message -> receives response with memory-hit transparency.
2. Owner submits execution goal -> specialist delegation emits timeline -> results returned.
3. High-impact delegation -> explicit approval interruption -> approval decision -> resumed execution.
4. Owner manages specialist configs in Agent Studio -> changes immediately affect delegation behavior.
5. Owner/member and cross-workspace boundaries remain enforced across all routes.
6. API restart -> invitations/approvals/audit/memory and agent run-event replay data remain available.

### Edge Cases
- Approval decision race while user retries execution submission.
- Replay resume from stale `last_seq` value after reconnect.
- Member attempting owner-only specialist edit path.
- Backend adapter fallback misconfiguration that could bypass secure mode.

## Acceptance Criteria

### Functional
- [ ] Companion, execution, and agent-studio routes execute full API-backed workflows.
- [x] Durable invitations/approvals/audit history survives process restarts.
- [x] Run-event replay (`agent_run_id`, `last_seq`) survives process restarts with deterministic ordering.
- [x] Memory retrieval behaves consistently across SQLite and Postgres/Supabase adapters.
- [ ] Approval-required flow is visible and recoverable in UI without manual API calls.

### Non-Functional
- [x] UI remains usable on modern desktop and mobile browsers with responsive verification.
- [x] `chat_orchestration_p95_ms <= 350` under benchmark protocol.
- [x] `memory_topk_retrieval_p95_ms <= 120` under benchmark protocol.
- [x] No high-severity security findings remain on v0.1 checklist.
- [x] Merge to `main` is technically impossible unless GitHub required CI checks are green.
- [x] Coverage reporting includes API, web, and worker codepaths on every PR to `main`.

### Quality Gates
- [x] `make lint` passes.
- [x] `make typecheck` passes.
- [x] `make coverage-all` passes and enforces coverage for API + web + worker (no surface excluded).
- [x] Coverage threshold is >= 90% for API, web, and worker.
- [x] `make check` passes.
- [x] Playwright browser contract tests pass in CI (`make web-browser-contract`).
- [x] Supabase RLS tests pass in CI as a required PR gate.
- [x] SQLite encrypted-vector compatibility checks pass in CI.
- [x] GitHub branch protection on `main` enforces required CI checks and blocks direct push merges.

### Remaining External Actions
- [ ] Wire web route interactions to live API calls through server functions (current UI shell and tests are in place).

### Branch Protection Verification (2026-02-11)
- Verified by: Codex via `gh api repos/locke69321/elara-ai/branches/main/protection`.
- Required checks include:
  - `ci / check`
  - `ci / coverage-all`
  - `ci / web-browser-contract`
  - `ci / app-authz-integration`
  - `ci / sqlite-compat`
  - `ci / semantic-pr-title`
  - `ci / commitlint`
  - `ci / branch-name`
- Enforcement state:
  - `required_status_checks.strict = true`
  - `required_pull_request_reviews.dismiss_stale_reviews = true`
  - `enforce_admins.enabled = true`
- Repository merge setting:
  - `allow_squash_merge = true`
  - `squash_merge_commit_title = PR_TITLE`

## Success Metrics

- 100% of critical dual-mode flows are executable through UI and API without placeholder-only interactions.
- 0 cross-workspace leakage regressions in API and adapter test suites.
- Deterministic replay and approval-resume flows pass with restart scenarios, including persisted run-event replay state.
- Operators can verify security and compatibility evidence from committed docs/scripts without ad-hoc manual steps.

## Risks & Mitigations

- Risk: persistence refactor breaks existing authz assumptions.
  - Mitigation: add cross-workspace regression tests before implementation.
- Risk: UI scope expands into redesign-only work.
  - Mitigation: constrain to workflow completeness + design-system tokens.
- Risk: benchmark instability in CI.
  - Mitigation: fixed fixture dataset and repeated-trial reporting.

## References

### Internal
- `docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md`
- `docs/architecture/dual-mode-core.md`
- `docs/security/threat-model-v1.md`
- `apps/web/src/routes/companion.tsx`
- `apps/web/src/routes/execution.tsx`
- `apps/web/src/routes/agent-studio.tsx`
- `apps/api/memory/store_sqlite.py`
- `apps/api/memory/store_postgres.py`
- `apps/api/auth/invitations.py`
- `apps/api/safety/approvals.py`
- `apps/api/audit/logging.py`
- `apps/api/events/outbox.py`
- `apps/web/package.json`
- `Makefile`

### Institutional Learnings
- `docs/solutions/security-issues/raw-invitation-tokens-in-audit-metadata-authentication-20260210.md`
- `docs/solutions/security-issues/cross-workspace-leakage-and-member-high-impact-delegation-authorization-20260211.md`

### External Documentation
- https://tanstack.com/start/latest/docs/framework/react/overview
- https://tanstack.com/start/latest/docs/framework/react/guide/code-execution-patterns
- https://tanstack.com/router/latest/docs/framework/react/guide/navigation
- https://tailwindcss.com/docs/theme
- https://tailwindcss.com/docs/responsive-design
- https://fastapi.tiangolo.com/

## Branch Changes Requested (Merged Addendum)

These branch/governance changes are now tracked in this canonical plan instead of a separate plan.

- Branch naming pattern:
  - `^(codex/)?(feat|fix|docs|chore|refactor|test|ci|build|perf|revert)\/[a-z0-9]+(?:-[a-z0-9]+)*$`
- PR title format:
  - `type(scope): summary`
  - `type: summary`
  - `type!: summary`
- Commit subject format:
  - Conventional Commits (`feat:`, `fix:`, `docs:`, etc. with optional scope and `!`)
- Required CI checks in branch protection:
  - `ci / semantic-pr-title`
  - `ci / commitlint`
  - `ci / branch-name`
  - existing quality checks from `docs/security/branch-protection-main.md`
- Merge policy requirements:
  - pull request required before merge
  - required checks must pass
  - branch must be up to date
  - stale approvals dismissed on new commits
  - direct pushes to `main` blocked
