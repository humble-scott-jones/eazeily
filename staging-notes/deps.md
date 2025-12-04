# staging/deps — Dependencies & Dockerfile

Purpose
- Ensure production image and runtime dependencies are correct and migrations run during release.

Commits to apply
- 0bb33a5 — Add missing production dependencies: gunicorn, psycopg
- 91dfe32 — Restore Python Dockerfile for Flask app

Files of interest
- `requirements.txt`
- `Dockerfile`
- CI workflows in `.github/workflows/ci.yml`

Steps
1. Checkout:
   - git checkout staging/deps
2. Cherry-pick required commits or manually update `requirements.txt` and `Dockerfile`.
3. Ensure Dockerfile or entrypoint runs migrations (`alembic upgrade head`) before starting the app.
4. Update CI to build the image and run tests against it.

Verification
- [ ] CI builds the Docker image successfully
- [ ] `alembic upgrade head` runs successfully in staging
- [ ] App starts and `/readyz` shows healthy
