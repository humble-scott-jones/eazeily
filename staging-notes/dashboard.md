# staging/dashboard — Activity feed & team features

Purpose
- Restore activity feed, ownership tags, and review routing automation.

Commits to apply
- 4aeac0c, a3a0252, bfa25e2, 20ffde8

Files of interest
- `static/dashboard.js`
- `templates/dashboard.html`
- `app.py` (team routing)

Steps
1. git checkout staging/dashboard
2. Cherry-pick commits or copy files
3. Run UI smoke tests and verify activity feed behavior in staging

Verification
- [ ] Dashboard displays activity and ownership tags
- [ ] Team approval routing works end-to-end
