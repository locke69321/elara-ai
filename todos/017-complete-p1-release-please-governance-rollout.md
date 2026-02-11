---
status: complete
priority: p1
issue_id: "017"
tags: [release, governance, ci, versioning]
dependencies: ["010"]
---

# Roll Out Release Please and Git Governance

## Scope

Execute the release governance plan in `docs/plans/2026-02-11-feat-release-please-v0-1-versioning-governance-plan.md`:
- Rebaseline initial release docs from `v0.1.0` to `v0.0.1`.
- Introduce release automation with Release Please.
- Enforce branch naming, PR title semantics, and commit message conventions.
- Update contributor guidance and branch protection documentation.

## Validation Targets

- `bash scripts/release/check-version-alignment.sh`
- `bash scripts/ci/validate-branch-name.sh <branch>`
- Dry-run Release Please command documented in `docs/releases/release-process.md`

## Completion Notes

- Added release automation and governance workflows:
  - `.github/workflows/release-please.yml`
  - `.github/workflows/semantic-pr-title.yml`
  - `.github/workflows/commitlint.yml`
  - `.github/workflows/branch-name.yml`
- Added governance configuration:
  - `release-please-config.json`
  - `.release-please-manifest.json`
  - `commitlint.config.cjs`
  - `scripts/ci/validate-branch-name.sh`
- Added version-alignment validation:
  - `scripts/release/check-version-alignment.sh`
- Re-baselined release docs from `v0.1.0` to `v0.0.1` and added a legacy path stub.
- Updated release/gov guidance in `AGENTS.md`, `docs/security/branch-protection-main.md`, and `.github/pull_request_template.md`.
- Captured release-please dry-run attempts and expected post-merge behavior in `docs/releases/release-process.md`.

## Remaining External Follow-ups

- Verify release-please creates and updates release PRs on `main` after this rollout is merged.
