#!/usr/bin/env bash
set -euo pipefail

if ! command -v gh >/dev/null 2>&1; then
  echo "[error] GitHub CLI (gh) is required. Install it from https://cli.github.com/ and run 'gh auth login'." >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[error] jq is required to build the API payload. Install jq and retry." >&2
  exit 1
fi

REPO=${GITHUB_REPOSITORY:-$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || true)}
if [[ -z "${REPO}" ]]; then
  echo "[error] Unable to determine repository. Set GITHUB_REPOSITORY=owner/name or run inside a cloned repo with gh configured." >&2
  exit 1
fi

BRANCH=${BRANCH_PROTECTION_BRANCH:-main}

# Default checks mirror the jobs in .github/workflows/ci.yml. Override by setting
# BRANCH_PROTECTION_CHECKS="CI / secret-scan,CI / tests" or a space-separated list.
DEFAULT_CHECKS=(
  "CI / secret-scan"
  "CI / tests"
  "CI / triage-smoke"
  "CI / smoke"
)

if [[ -n "${BRANCH_PROTECTION_CHECKS:-}" ]]; then
  IFS=',' read -r -a CHECKS <<< "${BRANCH_PROTECTION_CHECKS}"
else
  CHECKS=(${DEFAULT_CHECKS[@]})
fi

contexts_json=$(printf '%s\n' "${CHECKS[@]}" | jq -R . | jq -s .)

payload=$(jq -n \
  --argjson contexts "${contexts_json}" \
  '{
    required_status_checks: { strict: true, contexts: $contexts },
    enforce_admins: true,
    required_pull_request_reviews: {
      required_approving_review_count: 1,
      dismiss_stale_reviews: true,
      require_code_owner_reviews: false,
      require_last_push_approval: false,
      bypass_pull_request_allowances: { users: [], teams: [], apps: [] }
    },
    restrictions: null,
    required_linear_history: true,
    allow_force_pushes: false,
    allow_deletions: false,
    block_creations: true,
    required_conversation_resolution: true,
    lock_branch: false,
    allow_fork_pushes: false,
    allow_fork_syncing: true
  }')

echo "[info] Applying branch protection to ${REPO} on branch '${BRANCH}' with required checks: ${CHECKS[*]}"

gh api --method PUT "repos/${REPO}/branches/${BRANCH}/protection" --input <(echo "${payload}")

echo "[done] Branch protection updated. Validate in https://github.com/${REPO}/settings/branches"
