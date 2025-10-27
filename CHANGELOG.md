# Changelog

## 2025-10-26 — Phase 1 merge

- Restored landing assets and waitlist flow.
- Added admin UI and admin API endpoints for user management and reconciliation.
- Fixed and registered the review-response endpoint (`/api/generate-review-response`) and added `review_response.html` UI.
- Fixed `templates/index.html` and `static/app.js` to surface inline generator controls (avoids modal-only failures).
- Added tests: `tests/test_admin_users.py`, `tests/test_review_response.py` and Playwright e2e fixes.
- Cleaned up accidental pasted shell lines and fixed a small indentation bug in `app.py`.

Validation performed locally:
- Full pytest suite passed with `PORT=5001`.
- Playwright acceptance test passed locally after fixes.

Notes:
- Remove the `integration/main-refresh` branch after merging. CI should now run on `main`.
