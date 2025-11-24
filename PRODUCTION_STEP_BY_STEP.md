# Step-by-step production enablement status

This walkthrough aligns with the nine-step plan you requested. Each step lists what already exists in the repo, how to validate it, and how to finish wiring anything missing.

## 1) Secrets and environment variables
- **What exists:** Test-safe CI secrets list and copy/paste commands in `CI_SECRETS.md`; local `.env` guidance in `README_ENV.md`; Railway secrets/vars required by the deploy runbook in `DEPLOYMENT.md`.
- **How to verify:**
  - In GitHub, open **Settings → Secrets and variables → Actions** and confirm repository secrets match the list in `CI_SECRETS.md` (no values are viewable but names should exist). For environment-scoped secrets, open **Environments → staging/production** and check the same keys as listed in `DEPLOYMENT.md`.
  - Locally, ensure you have a `.env` by copying `.env.example` or `.env.dev`, then load it with `export $(cat .env | xargs)` before running the app.
- **If missing:**
  - Add the CI defaults with `gh secret set ...` from `CI_SECRETS.md`.
  - Add Railway deploy tokens and app secrets (`RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID_*`, `RAILWAY_TOKEN_*`, `SECRET_KEY`, Stripe/OpenAI keys, `ADMIN_EMAILS`, optional `GITHUB_FEEDBACK_*`, `DATABASE_URL` if Postgres) to the `staging` and `production` environments per `DEPLOYMENT.md`.
  - Keep the same app-secret names in Railway environment variables so deploys use them automatically.

## 2) CI gating on `main`
- **What exists:** A branch-protection helper script that sets required checks matching `.github/workflows/ci.yml` and blocks force/direct pushes.
- **How to verify:** Run `./scripts/apply_branch_protection.sh` (requires `gh` + `jq`) and then view GitHub **Settings → Branches** to confirm `main` shows required checks: `CI / secret-scan`, `CI / tests`, `CI / triage-smoke`, `CI / smoke`.
- **If missing:** Rerun the script with overrides as needed (e.g., `BRANCH_PROTECTION_CHECKS="CI / tests,CI / smoke"`).

## 3) Railway staging/production pipeline
- **What exists:** `.github/workflows/deploy-railway.yml` deploys on push to `main` (staging), on release publish (production), or manually via `workflow_dispatch` with an environment choice. `DEPLOYMENT.md` documents the required secrets and rollback commands.
- **How to verify:**
  - In GitHub Actions, open the workflow and confirm the triggers (push to `main`, release publish, manual dispatch) and that the jobs target the `staging` and `production` environments.
  - Dry-run a manual dispatch to staging after secrets are present to confirm Railway CLI login and `railway up` succeed.
- **If missing:** Add the Railway IDs/tokens to GitHub environment secrets and mirror app secrets inside Railway. Use the rollback commands in `DEPLOYMENT.md` to test reverting a deployment after a smoke ping to `/health`.

## 4) Local environment, app run, and health checks
- **What exists:** `.env` templates and quick-start commands to run `python3 app.py`; built-in health endpoints `/healthz` (liveness) and `/readyz` (readiness with DB/Stripe/OpenAI/GitHub checks) that back the legacy `/health` route.
- **How to verify:**
  - Copy `.env.dev` to `.env`, install requirements, run `python3 app.py`, and curl `http://127.0.0.1:5001/healthz` and `/readyz` to ensure the server starts and the DB check passes.
  - Use `./scripts/e2e_run.sh` or `make e2e` for the bundled smoke test runner.
- **If missing:** Re-create `.env` from the template, ensure SQLite file permissions allow writes, and confirm ports match `PORT` in `.env`.

## 5) Stripe configuration
- **What exists:** `README_STRIPE.md` with copy/paste commands for local webhook listening, dev user seeding, and endpoint smoke checks; reminders to use Stripe **test** keys locally and **live** keys in production.
- **How to verify:**
  - Run `stripe listen --forward-to http://localhost:5001/api/stripe-webhook` and copy the printed `whsec_...` into `STRIPE_WEBHOOK_SECRET`.
  - Start the app, hit `/api/stripe-publishable-key`, and confirm a JSON response containing your test publishable key.
- **If missing:** Fill `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_ID/STRIPE_TEST_PRICE_ID`, and `STRIPE_WEBHOOK_SECRET` in the relevant `.env`/environment secrets. For production, swap to live keys and the hosted webhook signing secret.

## 6) Database choice and migrations
- **What exists:** Runbook notes that dev runs on SQLite, while staging/production should use managed Postgres on Railway. Alembic directory is present for migrations.
- **How to verify:**
  - Check whether `DATABASE_URL` is set in staging/production environment secrets and in Railway env vars.
  - If using SQLite locally, ensure `togetherly.db` is created and writable when the app starts.
- **If missing:**
  - Provision Railway Postgres, set `DATABASE_URL` per environment, and add Alembic migration commands to your deploy flow (e.g., a pre-deploy step or manual run) before switching traffic.
  - Establish a backup/restore test for the chosen database.

## 7) Monitoring, alerting, and health probes
- **What exists:** Monitoring guide with metrics to track; health endpoints already return status plus dependency checks.
- **How to verify:**
  - Point Railway health checks to `/health` (alias for `/readyz`) and confirm 200 responses after deploy.
  - Configure an uptime probe (e.g., GitHub scheduled action or external monitor) hitting `/healthz`.
- **If missing:** Add exception tracking (e.g., Sentry) and create dashboards/alerts for the key metrics listed in `MONITORING.md`.

## 8) Security baseline
- **What exists:** Security best-practice guide covering auth, session settings, rate limiting, CSRF, and logging guidance.
- **How to verify:** Review that production config enforces HTTPS, secure cookies, and rate limiting on sensitive endpoints; ensure secret scanning (Gitleaks) remains enabled via the CI job.
- **If missing:** Apply the recommended headers/session settings, wire Flask-Limiter or equivalent, and keep secrets in GitHub/Railway env vars only.

## 9) Launch polish, runbooks, and checklists
- **What exists:** Launch quick reference plus detailed launch checklist/runbooks covering secrets, CI gating, deployment, backups, monitoring, health checks, domain/TLS, rate limiting, payments, and runbooks/SLOs.
- **How to verify:**
  - Walk through the “must-haves” table in `LAUNCH_CHECKLIST_QUICK_REF.md` and create issues from the linked templates.
  - Confirm rollout/rollback steps in `DEPLOYMENT.md` and incident/runbook docs are accessible to the team.
- **If missing:** Prioritize the must-haves list, finalize domain/TLS, ensure Stripe pricing/webhooks are live, and publish runbooks + SLOs before launch.

## Local test status (this run)
- `pytest -q -m "not e2e and not slow"` currently fails. The top issues are a `voice_profile` variable missing in `generator.py`, dev-mode toggles returning `False`, and `/api/generate` returning 500s in multiple flows. See the test output in the latest run for exact failures.
