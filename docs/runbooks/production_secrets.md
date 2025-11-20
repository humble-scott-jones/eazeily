# Production & Staging Secrets

Authoritative list of secrets/env vars and how to manage them safely. Keep staging and production aligned except for actual secret values.

## Required secrets
- Feedback → GitHub: `GITHUB_FEEDBACK_TOKEN`, `GITHUB_FEEDBACK_REPO`, `GITHUB_FEEDBACK_TEMPLATE_GENERAL`, `GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN`, `GITHUB_FEEDBACK_TIMEOUT`
- Stripe: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`, `STRIPE_PRICE_ID`, `STRIPE_WEBHOOK_SECRET` (plus `STRIPE_TEST_PRICE_ID` for staging)
- OpenAI: `OPENAI_API_KEY`, optional `OPENAI_GENERATE_MODEL`
- Database: `DATABASE_URL` (Postgres) or `DB_PATH` (SQLite fallback)
- Core app: `SECRET_KEY`, `ADMIN_EMAILS`, `PORT`, optional toggles (`ALLOW_DEV_DEBUG`, `REELS_QUOTA_MONTHLY`, `TEAM_MEMBER_LIMIT`)

## Storage & rotation
- Store in a manager (1Password Secrets Automation, Doppler, AWS/GCP Secrets Manager) under namespaces `togetherly/staging/*` and `togetherly/production/*`.
- Track metadata per secret: owner, last rotated date, rotation cadence, and rollback contact.
- Rotate safely: stage → deploy → verify → promote to prod → delete old key.

### Quick rotation playbooks
- **GitHub PAT (`GITHUB_FEEDBACK_TOKEN`)**: fine-grained PAT with Issues read/write on target repo. Rotate quarterly or after incidents. Smoke with `scripts/feedback_smoke.sh` against staging, then prod; revoke old PAT.
- **Stripe keys/webhooks**: create restricted keys + per-env webhook signing secrets. Test webhook delivery on staging before promoting.
- **OpenAI key**: generate new key, test generator endpoints in staging, then prod, then delete old key.
- **Database creds**: create a new DB user/password with same perms; update staging `DATABASE_URL`, migrate, verify; promote to prod during low-traffic; drop old user after verification.
- **SECRET_KEY**: plan deploy because session reset. Rotate per env separately; confirm logins still work.

## Keeping environments in sync
- Use `.env.example` as the template. Derive `.env.staging` and `.env.production` locally for reference (never commit).
- Keep GitHub environment secrets updated for deploy (`staging` and `production` environments).
- When a PR adds or changes secrets, update this runbook and the PR checklist, and note it in `docs/changelog.md`.
