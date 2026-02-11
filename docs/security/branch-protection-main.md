# Branch Protection: `main`

## Required Settings

Configure branch protection in GitHub repository settings for `main`:

- Require a pull request before merging.
- Require branches to be up to date before merging.
- Dismiss stale pull request approvals when new commits are pushed.
- Block direct pushes to `main`.
- Require these status checks:
  - `ci / check`
  - `ci / coverage-all`
  - `ci / web-browser-contract`
  - `ci / app-authz-integration`
  - `ci / sqlite-compat`
  - `ci / semantic-pr-title`
  - `ci / commitlint`
  - `ci / branch-name`
- Enable "Default to PR title for squash merge commits" in repository settings.
- Release automation check (post-merge, not a PR required check):
  - `release-please / release-please`

## Verification

1. Open a PR with one intentionally failing check.
2. Confirm merge button is blocked.
3. Fix the check and confirm merge button is unblocked only after all required checks pass.

## Notes

Branch protection enforcement happens in GitHub settings, not in repository code.
