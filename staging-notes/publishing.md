# staging/publishing — Publishing & scheduling

Purpose
- Restore publishing queue, scheduling defaults, and platform-specific publishing behavior.

Commits to apply
- 715c8a5, ac289f8

Files of interest
- `app.py` (publishing logic)
- `static/dashboard.js` (queue UI)

Steps
1. git checkout staging/publishing
2. Cherry-pick commits
3. Deploy to staging and exercise scheduling/publishing flows

Verification
- [ ] Scheduled jobs are enqueued
- [ ] Worker picks up scheduled jobs and triggers publish actions
