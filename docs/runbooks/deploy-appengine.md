# App Engine deployment (staging & production)

Deploy flow:
- Push to `main` ➜ deploys to **staging**.
- Push tag `v*` (e.g., `v2025.11.0`) ➜ deploys to **production** after environment approval.
- Manual: use `workflow_dispatch` and choose an environment.

Workflow: `.github/workflows/deploy-appengine.yml` renders `deploy/appengine/app.yaml.tmpl` with per-environment secrets and runs `gcloud app deploy`.

## One-time setup
1) **App Engine setup per project**  
   - Create projects (e.g., `togetherly-staging`, `togetherly-production`).  
   - Run `gcloud app create --region us-central` once per project (region is immutable).  

2) **Service accounts**  
   - Create a deployer SA per project (`gae-deployer@<project>.iam.gserviceaccount.com`).  
   - Grants: `App Engine Admin`, `Cloud Build Service Account`, `Storage Admin`, `Service Account Token Creator` (for OIDC).  
   - Download JSON keys to store as GitHub secrets.  

3) **GitHub environments + secrets**  
   - Environments: `staging`, `production` (add required reviewers/approvals on production).  
   - Secrets required:  
     - `GCP_PROJECT_STAGING` / `GCP_PROJECT_PRODUCTION`  
     - `GCP_SA_KEY_STAGING` / `GCP_SA_KEY_PRODUCTION` (SA JSON)  
     - `STAGING_SECRET_KEY` / `PRODUCTION_SECRET_KEY`  
     - `STAGING_STRIPE_SECRET_KEY` / `PRODUCTION_STRIPE_SECRET_KEY`  
     - `STAGING_STRIPE_PUBLISHABLE_KEY` / `PRODUCTION_STRIPE_PUBLISHABLE_KEY`  
     - `STAGING_STRIPE_PRICE_ID` / `PRODUCTION_STRIPE_PRICE_ID`  
     - `STAGING_STRIPE_WEBHOOK_SECRET` / `PRODUCTION_STRIPE_WEBHOOK_SECRET`  
     - Optional per-env: `STAGING_OPENAI_API_KEY`, `STAGING_OPENAI_GENERATE_MODEL`, `STAGING_ADMIN_EMAILS`, `STAGING_GITHUB_FEEDBACK_TOKEN`, `STAGING_GITHUB_FEEDBACK_REPO`, `STAGING_GITHUB_FEEDBACK_TEMPLATE_GENERAL`, `STAGING_GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN`, `STAGING_GITHUB_FEEDBACK_TIMEOUT` (and production variants).  

> Secrets are not echoed in logs; `envsubst` writes a temp file in `/tmp/deploy`.

## Rollback
- List versions: `gcloud app versions list --service togetherly-production` (or `togetherly-staging`).  
- Roll traffic back: `gcloud app services set-traffic togetherly-production --splits <version>=1`.  
- If a tag caused a bad prod deploy, delete the tag and open a revert PR; re-tag once fixed.  

## Smoke checks
- Hit `https://<staging-domain>/__dev__/ping` after deploy.  
- Manually test generator + feedback path in staging.  
- Tail logs while debugging: `gcloud app logs tail -s togetherly-staging`.  

## Making config changes
- Update `deploy/appengine/app.yaml.tmpl` for new env vars or scaling settings.  
- Add matching secrets to both environments before merging to `main`.  
- Note the change in `docs/changelog.md` under staging; move it to production when you tag.  
