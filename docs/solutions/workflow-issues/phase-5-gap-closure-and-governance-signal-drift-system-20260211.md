---
module: System
date: 2026-02-11
problem_type: workflow_issue
component: development_workflow
symptoms:
  - "Replay access for legacy runs without ACL rows could be allowed instead of denied."
  - "Workspace membership and owner authorization behavior regressed after service restart."
  - "Web quality gates labeled as coverage/E2E/RLS did not always reflect executed runtime behavior or true DB policy coverage."
  - "Release-governance and branch-protection readiness were split across plans with drifted checklist state."
  - "v0.1 closure work lacked one canonical, verifiable execution artifact across API, web, worker, CI, and docs."
root_cause: missing_workflow_step
resolution_type: workflow_improvement
severity: high
tags: [phase5-gap-closure, release-governance, ci-signal-integrity, authorization-durability, compounding]
---

# Troubleshooting: Phase 5 Gap Closure And Governance Signal Drift

## Problem
PR #1 (`feat: complete v0.1 gap closure and governance rollout`) addressed a cross-cutting reliability and governance gap: security-sensitive authorization behavior and CI/release readiness signals were partially durable, partially mislabeled, and split across parallel planning artifacts. The result was high risk of false confidence at release time.

## Environment
- Module: System-wide (API, Web, Worker, CI, Release Governance)
- Runtime: FastAPI + TypeScript web app + GitHub Actions
- Affected Component: Development workflow and release readiness controls
- PR scope source: `gh pr view 1` / `gh pr diff 1 --name-only`
- Scope size: 88 files changed, +6878 / -350
- Date solved: 2026-02-11

## Symptoms
- Replay auth path treated missing persisted ACL state as non-failing in legacy scenarios, creating an authorization bypass risk.
- Workspace member/owner state could diverge from persisted truth after restart, including owner takeover risk.
- Web "coverage" and "e2e" naming/signals did not consistently prove runtime execution of route modules.
- A "supabase-rls" gate validated app-layer authz logic, not database RLS policy enforcement.
- Branch-protection/release-governance status drifted between two active plan docs, weakening single-source release confidence.

## What Didn't Work

**Attempted approach 1:** In-memory-first authorization state without full startup hydration.
- **Why it failed:** Persistent data existed, but runtime authorization maps were incomplete on restart, causing access regressions and owner-claim inconsistencies.

**Attempted approach 2:** Treating unknown replay ACL state as implicitly acceptable.
- **Why it failed:** Missing ACL rows for legacy runs became an authorization bypass instead of a deny-by-default decision.

**Attempted approach 3:** Filename/static-contract checks presented as runtime coverage/E2E/RLS guarantees.
- **Why it failed:** Check names and semantics overstated what was actually validated, allowing green CI with weaker assurance than implied.

**Attempted approach 4:** Split execution ownership across multiple same-day v0.1 plans.
- **Why it failed:** Checklist drift and dependency ambiguity reduced operational clarity for go/no-go decisions.

## Solution
Implemented a single PR-wide gap-closure program with durable auth state, deny-by-default replay semantics, execution-based web coverage signals, and governance automation.

**Representative code changes**:
```python
# apps/api/agents/runtime.py
persisted_authorization = self._outbox.is_run_access_allowed(
    agent_run_id=agent_run_id,
    actor_id=actor.user_id,
)
if persisted_authorization is not True:
    raise PermissionError("actor is not authorized to replay this run")
```

```python
# apps/api/auth/workspaces.py
self._connection.execute(
    """
    insert into workspace_owner_record (workspace_id, owner_id, created_at)
    values (?, ?, ?)
    """,
    (workspace_id, actor.user_id, datetime.now(timezone.utc).isoformat()),
)
```

```js
// apps/web/scripts/coverage_gate.mjs
const coverageArgs = [
  '--experimental-test-coverage',
  `--test-coverage-lines=${threshold}`,
  ...requiredExecutedFiles.map((file) => `--test-coverage-include=${file}`),
  '--test',
  ...testFiles,
]
```

```bash
# scripts/ci/validate-branch-name.sh
PATTERN='^(codex/)?(feat|fix|docs|chore|refactor|test|ci|build|perf|revert)/[a-z0-9]+(-[a-z0-9]+)*$'
```

**Workflow and governance outcomes**:
- Hardened replay auth and restart durability paths across API runtime/state services.
- Added/updated tests across e2e, integration, and unit layers for replay ACL, workspace owner/member persistence, and authz boundaries.
- Replaced misleading web coverage gating with execution-driven checks and route execution reporting.
- Renamed CI targets/jobs to match true scope (for example, `app-authz-integration`, `web-browser-contract`).
- Added release/governance automation: Release Please, semantic PR title, commitlint, and branch-name validation.
- Consolidated v0.1 closure into one canonical plan and reconciled branch-protection status against live GitHub settings.

**Commands run to scope this compound**:
```bash
gh pr view 1 --json title,body,files,commits,additions,deletions,changedFiles,statusCheckRollup
gh pr diff 1 --name-only
gh api repos/locke69321/elara-ai/branches/main/protection
```

## Why This Works
1. **Root cause control:** The fix treated the issue as a workflow-system defect, not isolated bugs, and closed gaps across auth durability, CI signal integrity, and release governance in one execution stream.
2. **Fail-closed semantics:** Replay and workspace authorization now default to deny when persisted authority is absent or contradictory.
3. **Signal integrity:** CI job names and checks now match what they actually validate, reducing false security and test confidence.
4. **Single ownership:** Canonical plan ownership and branch-protection verification removed drift in release readiness state.

## Prevention
- Require deny-by-default behavior whenever persisted authorization state is unknown.
- Treat restart behavior as a first-class acceptance path for all persisted services.
- Enforce naming integrity: gate names must match validation semantics.
- Keep one canonical execution plan per release milestone; reference-only docs must be explicitly superseded.
- Add `gh api` verification snapshots for branch protection and required checks during release-readiness updates.
- Preserve outside-in TDD layering (e2e -> integration -> unit) for cross-cutting workflow changes.

## Related Issues
- See also: [cross-workspace-leakage-and-member-high-impact-delegation-authorization-20260211.md](../security-issues/cross-workspace-leakage-and-member-high-impact-delegation-authorization-20260211.md)
- See also: [raw-invitation-tokens-in-audit-metadata-authentication-20260210.md](../security-issues/raw-invitation-tokens-in-audit-metadata-authentication-20260210.md)
