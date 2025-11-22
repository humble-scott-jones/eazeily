# GitHub workflow and code review hygiene

This repository already includes PR templates and extensive testing docs. The checklist below keeps pull requests small, reviewable, and low-risk while minimizing merge conflicts.

## Branching and pull requests
- Protect `main` with required status checks and at least one approving review; enable "Require branches to be up to date" so PRs auto-update before merge.
- Create a short-lived feature branch per task (e.g., `feature/<ticket>`). Keep one PR per branch; push review feedback commits to the same branch rather than opening new PRs.
- Prefer **squash-merge** for a clean history. Enable **auto-merge** so GitHub merges as soon as checks + approvals pass.
- Rebase your branch onto `main` before requesting review (or enable GitHub's "Update branch" button) to avoid drift.
- Close stale branches after merge to reduce accidental rebases against old work.

## Review settings and quality gates
- Require the existing test suite to pass on every PR (unit + integration) and block merges if checks fail.
- Add CODEOWNERS entries for critical areas so the right reviewers are requested automatically.
- Turn on **dismiss stale approvals** after new commits so reviewers re-acknowledge changes.
- Enable **linear history** and **signed commits** (optional) to keep provenance clear.

## Using Copilot/AI suggestions safely
- Apply AI suggestions locally and run tests before pushing; avoid committing directly from the GitHub UI without verification.
- Always read diffs produced by Copilot/CodePilot before committing to ensure they match intent and coding standards.
- For review suggestions, amend the existing branch/PR instead of creating a new one; keep commit messages meaningful so reviewers understand AI-assisted changes.

## Minimizing merge conflicts
- Keep PRs scoped and small; avoid unrelated refactors alongside feature work.
- Rebase frequently against `main` (or enable auto-branch updates) when the branch lives for more than a day.
- Update lockfiles and generated artifacts in separate PRs when possible to avoid noisy conflicts.
- Document new config or scripts in the repo so teammates do not recreate divergent local setups.

## Testing and release confidence
- Use the repository's `run_tests.sh` to execute the standard suite in a local virtualenv. It installs dependencies and runs pytest (UI smoke tests are gated behind `RUN_UI_SMOKE`).
- Follow the test pyramid in `TESTING.md`—add unit coverage for new logic and integration/E2E coverage for user flows.
- Block merges unless the PR passes required checks and meets coverage targets; run focused tests (`pytest -k <pattern>`) on changed areas before pushing.
- Before deploying, run the full suite (including optional UI smoke tests) and verify staging manually if the change is user-facing.

## Deployment workflow
- Use the existing deployment scripts (`deploy.sh`, `deploy-to-railway.sh`, or platform-specific guides) from a clean `main` after CI passes.
- Tag releases after successful production deploys; include links to the PR and test evidence in the release notes.
- Roll back by redeploying the previous tag or reverting the PR if a regression is found.
