## Summary

- What changed?
- Why was it needed?

## Testing

- [ ] `make check`
- [ ] Additional targeted tests (list below if applicable)

## Release & Governance Checklist

- [ ] Branch name matches: `^(codex/)?(feat|fix|docs|chore|refactor|test|ci|build|perf|revert)\/[a-z0-9]+(?:-[a-z0-9]+)*$`
- [ ] PR title follows Conventional Commits style (for example: `feat(scope): short summary`)
- [ ] Commit subjects are Conventional Commits compliant
- [ ] If versioning/release docs changed, `bash scripts/release/check-version-alignment.sh` passes
