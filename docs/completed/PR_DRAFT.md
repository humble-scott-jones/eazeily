# PR Draft — November 2025 Branch Sync

**Base branch:** `main`
**Head branch:** `integration/2025-11-sync` (to be pushed from local `feature/add-logo` after merges)

## Summary

- Merge the latest `feature/add-logo` work (team-seat management UI, team approval flows, inline admin tooling, launch asset updates).
- Add targeted backend coverage via `tests/test_team_approvals.py` to exercise the new `/api/team/approvals` endpoints and guard against regressions.
- Document the proposed merge order and validation steps in `docs/branch_sync_plan.md` so subsequent feature branches can be rebased cleanly.
- Ensure the Flask dev server, account page, and approvals workflow run end-to-end locally prior to integration.

## Testing & Verification

- `pytest tests/test_team_approvals.py -q`
- `pytest -q`
- Manual `/healthz` + `/account` smoke checks against the Flask dev server on `http://127.0.0.1:5001`

## Follow-ups

- Merge additional high-priority branches (`feature/db-compat`, deployment workflows) into the integration branch per the plan.
- Populate Railway + GitHub secrets (see Priority 0 checklist) before cutting a release.
- Re-run `scripts/feedback_smoke.sh --start-local` once secrets are wired to confirm the feedback-to-GitHub automation.
- Capture screenshots/Loom of the refreshed account + approvals experience for reviewers.
