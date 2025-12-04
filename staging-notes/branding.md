# staging/branding — Landing page & assets

Purpose
- Update branding to "Eazeily" (landing page, logos) in a low-risk way.

Commits to apply
- a6e1662 — Fix DB connection timeout issue and update branding to Eazeily

Files of interest
- `templates/landing.html`
- `static/eazeily-logo.svg`

Steps
1. git checkout staging/branding
2. If `a6e1662` includes unrelated changes (DB fixes), either cherry-pick selectively or copy only the landing files into the branch.
3. Push branch and deploy to staging.

Verification
- [ ] Landing page shows Eazeily logo and updated copy
- [ ] No regressions in `/readyz`
