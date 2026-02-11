#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FAILURES=0

require_contains() {
  local file="$1"
  local pattern="$2"
  local message="$3"
  if [[ ! -f "$ROOT_DIR/$file" ]]; then
    echo "FAIL: $message ($file not found)"
    FAILURES=$((FAILURES + 1))
    return
  fi
  if ! rg -q --fixed-strings "$pattern" "$ROOT_DIR/$file"; then
    echo "FAIL: $message ($file missing '$pattern')"
    FAILURES=$((FAILURES + 1))
  fi
}

require_absent() {
  local file="$1"
  local pattern="$2"
  local message="$3"
  if [[ ! -f "$ROOT_DIR/$file" ]]; then
    echo "FAIL: $message ($file not found)"
    FAILURES=$((FAILURES + 1))
    return
  fi
  if rg -q --fixed-strings "$pattern" "$ROOT_DIR/$file"; then
    echo "FAIL: $message ($file still contains '$pattern')"
    FAILURES=$((FAILURES + 1))
  fi
}

require_exists() {
  local file="$1"
  local message="$2"
  if [[ ! -f "$ROOT_DIR/$file" ]]; then
    echo "FAIL: $message ($file not found)"
    FAILURES=$((FAILURES + 1))
  fi
}

require_exists "CHANGELOG.md" "changelog must exist"
require_exists "docs/releases/v0.0.1-initial-publish.md" "re-baselined initial release notes must exist"
require_exists "docs/releases/v0.1.0-initial-publish.md" "legacy path must remain as redirect/reference stub"
require_exists "apps/web/src/components/app-shell.tsx" "app shell source must exist"
require_exists "docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md" "gap closure plan must exist"
require_exists "docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md" "base dual-mode plan must exist"

require_contains "CHANGELOG.md" "## v0.0.1 - Initial Public Publish" "initial publish version must be re-baselined"
require_contains "CHANGELOG.md" "docs/releases/v0.0.1-initial-publish.md" "changelog must point to re-baselined release note path"
require_absent "CHANGELOG.md" "## v0.1.0 - Initial Public Publish" "old initial publish version heading must be removed"
require_absent "CHANGELOG.md" "docs/releases/v0.1.0-initial-publish.md" "old release note path must be removed from changelog"

require_contains "docs/releases/v0.0.1-initial-publish.md" "# v0.0.1 - Initial Public Publish" "release note title must match v0.0.1 baseline"
require_contains "docs/releases/v0.1.0-initial-publish.md" "Moved to: docs/releases/v0.0.1-initial-publish.md" "legacy release note path must redirect to new path"

require_contains "apps/web/src/components/app-shell.tsx" "Elara Dual Mode v0.1" "product shell heading must reflect v0.1 stream"
require_absent "apps/web/src/components/app-shell.tsx" "Elara Dual Mode v1" "product shell heading must not reference v1"

require_contains "docs/plans/2026-02-11-feat-dual-mode-v1-gap-closure-plan.md" "v0.1" "gap closure plan text must reference v0.1 stream"
require_contains "docs/plans/2026-02-10-feat-agent-native-companion-dual-mode-v1-plan.md" "v0.1" "dual-mode baseline plan text must reference v0.1 stream"

if [[ "$FAILURES" -gt 0 ]]; then
  echo
  echo "Version alignment checks failed ($FAILURES issue(s))."
  exit 1
fi

echo "Version alignment checks passed."
