# Deploy Changelog (Staging vs Production)

Source of truth for what is deployed where. Keep this file updated as PRs land on `main` and when production releases are tagged.

## How to use
- After merging to `main`, add a bullet under **Staging (next release)** with the PR/issue link and short description.
- When cutting a production release tag (e.g., `v2025.11.0`), move those bullets into a new production entry and add any rollback/link notes.
- If a change is reverted, mark it in both sections so staging/prod stay accurate.

## Staging (next release)
- Added App Engine deploy workflow (`.github/workflows/deploy-appengine.yml`) with main ➜ staging and tag ➜ production promotion, plus runbooks for deploy + secrets.

## Production releases

### 2025-10-26 — Phase 1 merge
- Restored landing assets and waitlist flow.
- Added admin UI and admin API endpoints for user management and reconciliation.
- Fixed and registered the review-response endpoint (`/api/generate-review-response`) and added `review_response.html` UI.
- Fixed `templates/index.html` and `static/app.js` to surface inline generator controls (avoids modal-only failures).
- Added tests: `tests/test_admin_users.py`, `tests/test_review_response.py` and Playwright e2e fixes.
- Cleaned up accidental pasted shell lines and fixed a small indentation bug in `app.py`.
