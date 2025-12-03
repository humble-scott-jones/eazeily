<!-- Please use this template to create PRs against the integration branch by default -->

## Summary

Brief description of changes and the motivation.

## Notes about base branch

This repository uses `integration/2025-11-sync` as the primary integration branch where CI and acceptance tests run. When creating a PR please set the base branch to `integration/2025-11-sync` unless you specifically intend to target `main` or `staging` for a release.

## Checklist
- [ ] Tests pass locally
- [ ] CI is green
- [ ] If this affects deploys, coordinate with the infra owner before merging
# Summary

- [ ] What changed and why? Keep it tight (bullets, not paragraphs).
- [ ] Link the related issue/epic.

# Testing

- [ ] `pytest -q`
- [ ] Optional: `RUN_E2E=1 pytest -q` (only if e2e touched)
- [ ] Manual verification (describe): ...

# Deployment / Release Readiness

- [ ] No migrations introduced, or migrations documented
- [ ] Secrets/env vars documented in `docs/runbooks/production_secrets.md` (if added/changed)
- [ ] Added/updated `docs/changelog.md` (what’s in staging vs production)
- [ ] Rollback noted or unchanged; if changed, link to runbook entry

# Notes for Reviewer
#
# [ ] CI green and branch rebased on latest `integration/2025-11-sync`
- [ ] Any flags/toggles that should stay off in production?
