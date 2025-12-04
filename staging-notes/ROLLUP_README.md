# Rollout README

This directory contains per-branch implementation notes and checklists to perform an incremental staged rollout.

Files included
- `db-fix.md` — DB connection and migration fixes (critical)
- `deps.md` — dependencies and Dockerfile
- `branding.md` — landing page updates
- `generator.md` — content generator features
- `voice-profile.md` — voice profile onboarding
- `dashboard.md` — team and activity feed
- `publishing.md` — scheduling and publish queue
- `tests.md` — CI and smoke test work

General workflow
1. Work on one staging/* branch at a time.
2. Cherry-pick the commits listed in the notes or copy only the files required.
3. Run tests locally and in CI, then deploy to staging and validate.
4. Merge PR into `staging/rollout-2025-12-04` when green.
5. Promote `staging/rollout-2025-12-04` to production when all features are validated.
