#!/usr/bin/env bash
set -euo pipefail

BRANCH_NAME="${1:-}"
PATTERN='^(codex/)?(feat|fix|docs|chore|refactor|test|ci|build|perf|revert)/[a-z0-9]+(-[a-z0-9]+)*$'

if [[ -z "$BRANCH_NAME" ]]; then
  echo "Branch name is required as the first argument."
  exit 1
fi

if [[ "$BRANCH_NAME" =~ $PATTERN ]]; then
  echo "Branch name is valid: $BRANCH_NAME"
  exit 0
fi

echo "Invalid branch name: $BRANCH_NAME"
echo "Expected pattern: $PATTERN"
echo "Examples:"
echo "  feat/release-governance"
echo "  fix/approval-replay-scope"
echo "  codex/chore/update-doc-links"
exit 1
