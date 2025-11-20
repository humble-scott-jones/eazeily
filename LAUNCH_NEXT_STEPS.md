# Launch Readiness – November 2025

This document replaces the earlier launch checklist snapshot. It captures only what still needs to happen from our current state (feedback capture, GitHub automation wiring, working Flask app + tests) to a production-ready launch.

## Current Snapshot

- ✅ Core product experience (wizard, dashboard, generator, feedback flows) works locally; unit tests (`pytest -q`) are green.
- ✅ Feedback ➜ GitHub automation exists but is disabled until PAT/env vars are populated.
- ⚠️ No automated deployment pipeline or dedicated staging/prod environments yet.
- ⚠️ SQLite is still the primary datastore with no automated backups or migration path.
- ⚠️ Monitoring/alerting, health checks, and performance baselines are not configured.
- ⚠️ Launch landing page, payments, and runbooks still reference draft content.

Use the sections below to open new GitHub issues (one per numbered item). Suggested priority order is top → bottom inside each block.

---

## Priority 0 – Unlock the new feedback pipeline (This Week)

> ✅ Detailed how-to: `docs/runbooks/priority0.md`

1. **Wire production secrets & credentials**  
   - Create/update `.env` (or hosting secrets) with `GITHUB_FEEDBACK_*`, OpenAI, Stripe, and database credentials.  
   - Store long-lived secrets in a proper manager (e.g., 1Password, Doppler, AWS/GCP Secrets).  
   - Document rotation steps and owners.

2. **Enforce CI gating on `main`**  
   - Ensure `.github/workflows/ci.yml` runs lint + pytest on pushes/PRs.  
   - Turn on required status checks + 1 review before merge.  
   - Block force-pushes to protected branches.

3. **Smoke-test the feedback-to-GitHub flow end-to-end**  
   - Use staging PAT + repo to submit a dashboard note and thumbs-down report (`scripts/feedback_smoke.sh --start-local` can automate this locally).  
   - Verify the correct templates (`user-feedback`, `thumbs-down`) are used, labels apply, and payload includes plan length + caption snapshots.

---

## Priority 1 – Infrastructure & Reliability (Before inviting external beta)

4. **Deployment pipeline + environment separation**  
   - ✅ Hosting: Railway project with `staging` + `production` environments (identical config; only secrets differ).  
   - ✅ GitHub Actions deploy workflow: merge to `main` ➜ staging deploy; tagged release ➜ production deploy with approval gate. See `.github/workflows/deploy-railway.yml`.  
   - 🚧 Secrets: add `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID_STAGING`, `RAILWAY_SERVICE_ID_PRODUCTION`, `RAILWAY_TOKEN_STAGING`, `RAILWAY_TOKEN_PRODUCTION`, plus app env vars (`SECRET_KEY`, Stripe, OpenAI, feedback GitHub tokens, `ADMIN_EMAILS`) to GitHub envs. Mirror app secrets inside each Railway environment.  
   - ✅ Rollback/runbook captured in `DEPLOYMENT.md` (Railway section). Use `railway deployments list` + `railway deployment rollback <id> --environment staging|production`.

5. **Database durability + migration story**  
   - Decide whether to stay on SQLite (with automated backups) or migrate to managed Postgres.  
   - Add nightly backup job + restore test.  
   - Introduce Alembic (or similar) for schema migrations with documented rollback.

6. **Monitoring, logging, and alerting**  
   - Add Sentry (or similar) for exception tracking.  
   - Stand up uptime check (Better Uptime, Pingdom, or GitHub scheduled job hitting `/healthz`).  
   - Define key metrics (error rate, request latency, queue depth) and wire alerts to Slack/email.

7. **Health checks & platform readiness**  
   - Implement `/healthz` (liveness) and `/readyz` (readiness) endpoints that cover DB connection + critical dependencies.  
   - Teach your load balancer to use those endpoints.  
   - Document non-200 responses + remediation steps.

8. **Security baseline (access controls + rate limiting)**  
   - Inventory all service accounts and ensure least privilege.  
   - Add simple rate limiting (Flask-Limiter or reverse proxy) for `/api/generate`, feedback endpoints, and auth flows.  
   - Enable secret scanning (GitHub Advanced Security or Gitleaks) in CI.

---

## Priority 2 – Launch-Blocking Product Work (Before marketing push)

9. **Domain, TLS, and canonical URLs**  
   - Purchase/assign the production domain.  
   - Terminate TLS via hosting provider or managed certs.  
   - Force HTTPS + www/non-www canonicalization.  
   - Update meta/OpenGraph tags for sharing.

10. **Payments & entitlements**  
   - Finalize Stripe pricing IDs, webhooks, and upgrade flows.  
   - QA happy path + cancellation/refund in staging with live keys.  
   - Document how entitlements map to app-level flags (e.g., reels quota, feature unlocks).

11. **Performance baseline + load test**  
   - Define target traffic assumptions (e.g., 50 concurrent creators).  
   - Use Locust/K6 to simulate generator + feedback endpoints.  
   - Capture CPU/memory profiles; fix hot spots; record baseline metrics in repo.

12. **Rollout & rollback plan**  
   - Decide on launch cohorts (internal, friends/family, public).  
   - Write an explicit playbook: preflight checks, metrics to watch, instant rollback procedure.  
   - Rehearse once on staging.

---

## Priority 3 – Operations & GTM Readiness

13. **Runbooks, on-call, and SLOs**  
   - Draft quick-response guides for: failed deploy, Stripe outage, OpenAI degradation, DB locked.  
   - Define SLOs (latency, error rate, response time) and escalation path.  
   - Share in a `RUNBOOKS/` folder + Notion/Drive.

14. **Landing page, analytics, and messaging**  
   - Replace placeholder content with final copy, industry logos, and founder story.  
   - Wire analytics (GA4, PostHog, or Plausible) + conversion goals.  
   - Add waitlist/early access capture if GA is staggered.

15. **Post-launch instrumentation**  
   - Decide on weekly KPI report (signups, activated users, retention, feedback volume).  
   - Automate exports/dashboards so you can react during week 1.  
   - Schedule a day-7 postmortem + retro slot.

---

## Tracking & Next Steps

- Create one GitHub issue per numbered line (or convert to Epics/Projects) and link back to this document.
- Update this doc at the end of each sprint to reflect real status (✅ / 🚧 / 🟥).
- When all Priority 0–2 items are ✅, schedule the launch rehearsal.
- Process refs: branching/PR hygiene in `docs/branching.md`; PR template in `.github/pull_request_template.md`; staging vs production tracking in `docs/changelog.md`.
