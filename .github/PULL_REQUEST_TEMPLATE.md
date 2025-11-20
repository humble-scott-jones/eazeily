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

- [ ] CI green and branch rebased on latest `main`
- [ ] Any flags/toggles that should stay off in production?
