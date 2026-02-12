# Release Process (Release Please)

## Configuration

Release automation is configured through:
- `.github/workflows/release-please.yml`
- `release-please-config.json`
- `.release-please-manifest.json`

Current baseline manifest:
- `"." : "0.0.1"`

Pre-1.0 behavior:
- `bump-minor-pre-major: true`
- `bump-patch-for-minor-pre-major: true`

## Local Validation Attempts

Command used:

```bash
pnpm dlx release-please release-pr \
  --repo-url=locke69321/elara-ai \
  --target-branch=main \
  --dry-run \
  --config-file=release-please-config.json \
  --manifest-file=.release-please-manifest.json
```

Observed result:
- Failed before PR synthesis because `.release-please-manifest.json` is not yet present on remote `main` (expected before first merge of this rollout).

Command used:

```bash
pnpm dlx release-please release-pr \
  --repo-url=locke69321/elara-ai \
  --target-branch=main \
  --dry-run \
  --release-type=simple \
  --package-name=elara-ai \
  --changelog-path=CHANGELOG.md \
  --latest-tag-version=0.0.1 \
  --latest-tag-name=v0.0.1 \
  --latest-tag-sha=$(git rev-list --max-parents=0 HEAD)
```

Observed result:
- Failed with GitHub API `401 Bad credentials` in this local environment.

## Expected Behavior After Merge

Once this rollout is merged to `main` and GitHub Actions runs with repository `GITHUB_TOKEN`:
1. Release Please opens or updates a release PR targeting `main`.
2. With current Conventional Commit history and `0.0.1` baseline, the next release should be `v0.1.0` when at least one `feat:` commit is included.
3. `CHANGELOG.md` is updated by Release Please in the release PR.
4. Merging the release PR creates the `v0.1.0` tag and corresponding GitHub release.

## Operator Check

After merge to `main`, verify:
1. `release-please / release-please` workflow succeeds.
2. A release PR exists with the expected target version.
3. `CHANGELOG.md` in the release PR includes entries derived from conventional commit subjects.
