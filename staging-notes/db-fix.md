# staging/db-fix — Database & runtime fixes

Purpose
- Fix Postgres connection errors (Railway `?timeout=` param vs psycopg v3 expectations).
- Make the staging branch a minimal, testable unit to validate database connectivity and migrations.

Commits to apply
- eb55b3a — Fix DB connection: map timeout to connect_timeout
- 1fc4ed0 — Robust fix for DB timeout param
- a9b508d — Fix NameError in Postgres wrapper: import dict_row

Files of interest
- `app.py` (Postgres wrapper, _connect_db() and init_db() logic)
- `alembic/` (migrations)

Steps (safe, repeatable)
1. Checkout branch:
   - git checkout staging/db-fix
2. Apply commits (preferred: cherry-pick each commit):
   - git cherry-pick eb55b3a 1fc4ed0 a9b508d
   - Resolve conflicts if any (likely in `app.py`): edit file, git add, git cherry-pick --continue
3. Ensure `app.py` replaces `?timeout=` and `&timeout=` with `connect_timeout` before calling `psycopg.connect()`.
4. Migration: ensure Alembic migrations will run in staging. Locally test:
   - pip install -r requirements.txt
   - alembic upgrade head
5. Deploy to staging and validate readiness and logs.

Verification checklist
- [ ] `/readyz` shows `db.status: healthy`
- [ ] `/healthz` returns 200
- [ ] No psycopg OperationalError logs about `timeout`

Notes
- If your deployment relies on `init_db()` for schema creation, note that `init_db()` currently short-circuits when `USE_POSTGRES` is true and expects migrations. Prefer Alembic for production.
