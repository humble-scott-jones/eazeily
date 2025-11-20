# Railway + Google App Engine Secrets Guide

This guide uses Railway now and Google App Engine (GAE) later. Managed Postgres is used in staging/production; SQLite stays for local dev.

## Railway (staging → production)

1) In Railway, create a PostgreSQL add-on per environment. Railway will supply `DATABASE_URL`.
2) Set env vars (run once per environment; replace placeholders):

```bash
# Choose environment
railway env use <staging-env-id>  # repeat with prod after staging verification

# Core + DB + quotas
railway variables set \
  SECRET_KEY=<generate_random> \
  FLASK_ENV=production \
  PORT=8080 \
  ADMIN_EMAILS=you@example.com \
  DATABASE_URL=${DATABASE_URL} \
  REELS_QUOTA_MONTHLY=30 \
  TEAM_MEMBER_LIMIT=10

# Stripe
railway variables set \
  STRIPE_SECRET_KEY=<sk_live_or_test> \
  STRIPE_PUBLISHABLE_KEY=<pk_live_or_test> \
  STRIPE_PRICE_ID=<price_live_or_test> \
  STRIPE_TEST_PRICE_ID=<price_test_if_kept> \
  STRIPE_WEBHOOK_SECRET=<whsec_live_or_test> \
  STRIPE_SUCCESS_URL=https://<env-domain>/ \
  STRIPE_CANCEL_URL=https://<env-domain>/

# OpenAI
railway variables set \
  OPENAI_API_KEY=<openai_key> \
  OPENAI_GENERATE_MODEL=gpt-4o-mini

# GitHub feedback automation
railway variables set \
  GITHUB_FEEDBACK_TOKEN=<pat_with_issues_rw> \
  GITHUB_FEEDBACK_REPO=humble-scott-jones/swelly \
  GITHUB_FEEDBACK_TEMPLATE_GENERAL=user-feedback \
  GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN=thumbs-down \
  GITHUB_FEEDBACK_TIMEOUT=6.0
```

**Rotation:** add new value → redeploy → verify (run `./scripts/feedback_smoke.sh --env .env.feedback-smoke --base-url <staging>`) → delete old value → note `rotated_at`/`rotated_by` in your tracker.

## Local development

- Keep SQLite: `DB_PATH=swelly.db` in `.env.dev`/`.env`. No Postgres needed locally.

## Google App Engine (future)

- Create the same keys in GCP Secret Manager under `togetherly/staging/*` and `togetherly/production/*`.
- Map each secret to env vars for App Engine (console or `app.yaml` secret references):
  - `SECRET_KEY`, `ADMIN_EMAILS`, `PORT=8080`
  - `DATABASE_URL` (managed Postgres)
  - `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_ID`, `STRIPE_TEST_PRICE_ID` (if used), `STRIPE_WEBHOOK_SECRET`, `STRIPE_SUCCESS_URL`, `STRIPE_CANCEL_URL`
  - `OPENAI_API_KEY`, `OPENAI_GENERATE_MODEL`
  - `GITHUB_FEEDBACK_TOKEN`, `GITHUB_FEEDBACK_REPO`, `GITHUB_FEEDBACK_TEMPLATE_GENERAL`, `GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN`, `GITHUB_FEEDBACK_TIMEOUT`
  - `REELS_QUOTA_MONTHLY`, `TEAM_MEMBER_LIMIT`

**GAE rotation:** create a new secret version → deploy staging → verify → promote to production → disable old version once validated.
