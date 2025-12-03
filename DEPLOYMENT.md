# Deployment Runbook

## Overview

This runbook describes the deployment process for Togetherly, including pre-deployment checks, deployment strategies, and rollback procedures.

## Current CI/CD (Railway)

- **Platform:** Railway project with two environments: `staging` and `production`.
- **Triggers:** Push to `staging` deploys to staging; push to `main` deploys to production after manual environment approval; `workflow_dispatch` supports on-demand redeploys for either environment.
- **Workflow:** `.github/workflows/deploy-railway.yml` installs Railway CLI, logs in via service token, and runs `railway up` against the appropriate environment/service.
- **Required GitHub secrets:** `RAILWAY_PROJECT_ID`, `RAILWAY_SERVICE_ID_STAGING`, `RAILWAY_SERVICE_ID_PRODUCTION`, `RAILWAY_TOKEN_STAGING`, `RAILWAY_TOKEN_PRODUCTION`, plus app secrets per environment (`SECRET_KEY`, Stripe keys/price/webhook, `OPENAI_API_KEY`, `ADMIN_EMAILS`, optional `GITHUB_FEEDBACK_*`, `TEAM_MEMBER_LIMIT`, `PASSWORD_HASH_METHOD`, `DATABASE_URL` if using Postgres).
- **Railway environment vars:** Mirror the app secrets above inside each Railway environment; keep values identical across envs except for secrets/keys and webhook URLs. Healthcheck path uses `/health`.
- **Railway database vars:** Remove any legacy `DB_PATH` variable from Railway → Service → Variables so deployments **must** use the managed Postgres `DATABASE_URL`. Leaving `DB_PATH` defined allows Flask to fall back to SQLite if `DATABASE_URL` disappears, which silently diverges environments. Use the dashboard to delete the key; the CLI cannot remove it yet.
- **Rollback:** List deployments with `railway deployments list --project <project-id> --environment staging|production`; roll back with `railway deployment rollback <deployment-id> --project <project-id> --environment staging|production`. Validate with a smoke ping to `/health` after rollback.

## Current CI/CD (App Engine)

- **Platform:** Google App Engine with distinct staging and production projects.
- **Triggers:** Push to `staging` deploys to staging; push to `main` deploys to production after environment approval; `workflow_dispatch` supports on-demand redeploys for either environment.
- **Workflow:** `.github/workflows/deploy-appengine.yml` renders `deploy/appengine/app.yaml.tmpl` per environment and runs `gcloud app deploy` against the target project.
- **Required GitHub secrets:** `GCP_SA_KEY_STAGING`, `GCP_PROJECT_STAGING`, `GCP_SA_KEY_PRODUCTION`, `GCP_PROJECT_PRODUCTION`, plus the app secrets referenced in the workflow for each environment (`SECRET_KEY`, Stripe keys, `OPENAI_API_KEY`, `ADMIN_EMAILS`, `GITHUB_FEEDBACK_*`, etc.).
- **Rollback:** Use App Engine version rollback via the Google Cloud console or `gcloud app versions list` / `gcloud app services set-traffic` to shift traffic back to the previous version.

## Environments

### Development
- **URL:** Local (http://localhost:5001)
- **Purpose:** Local development and testing
- **Database:** SQLite (togetherly.db)
- **Deploy Method:** Manual (`python app.py`)

### Staging
- **URL:** TBD (e.g., staging.togetherly.app)
- **Purpose:** Pre-production testing and validation
- **Database:** PostgreSQL (staging instance)
- **Deploy Method:** CI/CD on merge to `staging` branch
- **Access:** Internal team + QA

### Production
- **URL:** TBD (e.g., togetherly.app)
- **Purpose:** Live customer-facing application
- **Database:** PostgreSQL (production instance with backups)
- **Deploy Method:** CI/CD on merge to `main` branch with approval gates
- **Access:** Public
- **Stripe status:** Production currently uses Stripe *test* keys during the beta. Document any beta charges as $0 and plan a key rotation (publishable + secret + webhook) before enabling paid subscriptions.

## Pre-Deployment Checklist

Before deploying to production, ensure:

### Code Quality
- [ ] All CI checks pass (tests, linting, security scans)
- [ ] Code review approved by at least one team member
- [ ] No known critical or high-severity bugs
- [ ] Test coverage meets minimum threshold (80%)

### Testing
- [ ] Unit tests pass (100%)
- [ ] Integration tests pass on staging
- [ ] E2E tests pass on staging
- [ ] Manual smoke testing completed on staging
- [ ] Performance tests show no regressions

### Security
- [ ] Dependency vulnerability scan shows no critical issues
- [ ] Secrets rotated if needed
- [ ] Security headers configured
- [ ] HTTPS enforced
- [ ] No sensitive data in logs

### Database
- [ ] Database migrations tested on staging
- [ ] Migration rollback plan documented
- [ ] Database backup completed before migration
- [ ] Migration is backwards compatible OR downtime scheduled
- [ ] Data validation queries prepared

### Documentation
- [ ] CHANGELOG updated
- [ ] API documentation updated if endpoints changed
- [ ] Runbook updated if deployment process changed
- [ ] Customer-facing changes documented in release notes

### Monitoring
- [ ] Alerts configured for new features
- [ ] Dashboards updated with new metrics
- [ ] Log aggregation verified
- [ ] Health checks validate new functionality

### Communication
- [ ] Team notified of deployment window
- [ ] Stakeholders informed of expected changes
- [ ] Downtime window communicated if applicable
- [ ] On-call engineer identified

## Deployment Strategies

### Blue-Green Deployment (Recommended for Production)

**Overview:** Run two identical production environments (blue and green). Deploy to inactive environment, test, then switch traffic.

**Process:**
1. **Deploy to Green (inactive):**
   ```bash
   # Deploy new version to green environment
   ./scripts/deploy-green.sh
   ```

2. **Validate Green:**
   ```bash
   # Run smoke tests against green
   ./scripts/validate-deployment.sh --env green
   ```

3. **Switch Traffic:**
   ```bash
   # Gradually shift traffic: 10% -> 50% -> 100%
   ./scripts/switch-traffic.sh --to green --percentage 10
   # Monitor for 5 minutes
   ./scripts/switch-traffic.sh --to green --percentage 50
   # Monitor for 10 minutes
   ./scripts/switch-traffic.sh --to green --percentage 100
   ```

4. **Monitor:**
   - Watch error rates, latency, CPU, memory
   - Check application logs
   - Validate key user flows

5. **Rollback if needed:**
   ```bash
   ./scripts/switch-traffic.sh --to blue --percentage 100
   ```

**Advantages:**
- Zero-downtime deployment
- Easy rollback
- Production validation before full release

**Disadvantages:**
- Requires double infrastructure capacity
- Database migrations need special handling

### Canary Deployment (Alternative)

**Overview:** Deploy to small percentage of servers/users first, gradually increase.

**Process:**
1. Deploy to 5% of servers
2. Monitor for 15 minutes
3. Increase to 25%
4. Monitor for 15 minutes
5. Increase to 100%

**Use when:**
- Testing user-facing changes
- Validating performance under real load
- Gradual rollout of features

### Rolling Deployment

**Overview:** Update servers one at a time or in small batches.

**Process:**
1. Remove server from load balancer
2. Deploy new version
3. Run health checks
4. Add back to load balancer
5. Repeat for next server

**Use when:**
- Low-risk changes
- Infrastructure permits rolling updates

## Rollback Procedures

### Application Rollback

**Quick Rollback (< 5 minutes):**
```bash
# Blue-Green: Switch traffic back
./scripts/switch-traffic.sh --to blue --percentage 100

# Rolling: Deploy previous version
./scripts/deploy.sh --version previous

# Container-based: Roll back to previous image
kubectl rollout undo deployment/togetherly
```

**When to Rollback:**
- Error rate > 1%
- Response time p95 > 5 seconds
- Critical functionality broken
- Security vulnerability introduced
- Database corruption detected

**Rollback Checklist:**
- [ ] Identify issue and confirm rollback needed
- [ ] Notify team via incident channel
- [ ] Execute rollback command
- [ ] Verify rollback successful (error rate normalizes)
- [ ] Document incident for post-mortem
- [ ] Fix issue in development
- [ ] Re-deploy with fix

### Database Rollback

**Migration Rollback:**
```bash
# If migration has down migration
python scripts/migrate.py down

# If no down migration, restore from backup
./scripts/restore-db.sh --backup <timestamp>
```

**Prevention:**
- Always write reversible migrations
- Test migrations on staging data
- Keep backup before migration
- Make migrations backwards compatible when possible

## Database Migrations

Togetherly now uses Alembic for Postgres + SQLite parity. The config lives in `alembic.ini`, the env script in `alembic/env.py`, and versioned migrations in `alembic/versions/`.

### Everyday Workflow

```bash
source .venv/bin/activate
alembic revision -m "add my_table"
alembic upgrade head
```

- Run revisions against staging first; once validated, deploy and run `alembic upgrade head` in production (CI can run this step automatically).
- Never edit the generated revision IDs. Keep the linear chain intact: `20241005_01_initial` → `20241006_01_team_workflow` → `20241008_01_team_drafts` → …
- For emergency schema diffs, you can still use `pg_dump`/`pg_restore`, but prefer migrations to avoid full-database restores.

### Safe Migration Process

1. **Write Migration:**
   - Make migrations backwards compatible
   - Avoid locking tables (use online DDL)
   - Test on copy of production data

2. **Test on Staging:**
   ```bash
   # Run migration
   python scripts/migrate.py up
   
   # Validate data
   python scripts/validate-migration.py
   
   # Test rollback
   python scripts/migrate.py down
   python scripts/migrate.py up
   ```

3. **Backup Production:**
   ```bash
   # Create backup
   ./scripts/backup-db.sh --env production
   
   # Verify backup
   ./scripts/verify-backup.sh --backup <timestamp>
   ```

4. **Run Migration:**
   ```bash
   # During low-traffic period
   python scripts/migrate.py up --env production
   ```

5. **Validate:**
   ```bash
   # Run validation queries
   python scripts/validate-migration.py --env production
   ```

### Migration Safety Rules

- **Never:** Drop columns in same release (deprecate first)
- **Never:** Drop tables without data export
- **Never:** Rename columns without backwards compatibility
- **Always:** Add columns as nullable or with defaults
- **Always:** Create indexes concurrently (PostgreSQL)
- **Always:** Test rollback before production

## Deployment Commands

### Manual Deployment (Development)
```bash
# Start development server
source .venv/bin/activate
PORT=5001 python app.py
```

### CI/CD Deployment (Staging/Production)
Deployments are triggered automatically via GitHub Actions:

**Staging:**
- Trigger: Merge to `staging` branch
- Automatic deployment after tests pass

**Production:**
- Trigger: Merge to `main` branch OR manual approval
- Requires approval from designated approvers
- Deployment after all checks pass

### Deployment Scripts
```bash
# Deploy specific version
./scripts/deploy.sh --env production --version v1.2.3

# Deploy with database migration
./scripts/deploy.sh --env production --with-migration

# Check deployment status
./scripts/deployment-status.sh --env production

# Validate deployment
./scripts/validate-deployment.sh --env production
```

## Health Checks

### Application Health Endpoint
```bash
# Basic health check
curl https://togetherly.app/health

# Expected response
{
  "status": "healthy",
  "version": "1.2.3",
  "timestamp": "2025-10-26T14:00:00Z",
  "database": "connected",
  "services": {
    "stripe": "available",
    "openai": "available"
  }
}
```

### Validation Checks Post-Deployment
```bash
# Check critical user flows
./scripts/smoke-test.sh --env production

# Verify database connections
./scripts/check-db-health.sh --env production

# Validate external integrations
./scripts/check-integrations.sh --env production
```

## Monitoring During Deployment

### Key Metrics to Watch

1. **Error Rate:**
   - Normal: < 0.1%
   - Warning: > 0.5%
   - Critical: > 1%

2. **Response Time:**
   - Normal: p95 < 2 seconds
   - Warning: p95 > 3 seconds
   - Critical: p95 > 5 seconds

3. **Request Rate:**
   - Monitor for unexpected drops (indicates outage)
   - Monitor for unexpected spikes (indicates issue)

4. **Database:**
   - Connection pool utilization < 80%
   - Query time p95 < 500ms
   - No deadlocks

5. **Resource Usage:**
   - CPU < 70%
   - Memory < 80%
   - Disk space > 20% free

### Monitoring Dashboards
- **Application Dashboard:** Response times, error rates, throughput
- **Infrastructure Dashboard:** CPU, memory, disk, network
- **Database Dashboard:** Query performance, connections, locks
- **Business Metrics:** User signups, content generation, payments

## Post-Deployment

### Immediate (0-30 minutes)
- [ ] Verify deployment successful via health checks
- [ ] Monitor error rates and latency
- [ ] Check critical user flows
- [ ] Review logs for errors
- [ ] Validate database migrations

### Short-term (1-4 hours)
- [ ] Monitor metrics for anomalies
- [ ] Review customer feedback/support tickets
- [ ] Check for memory leaks or resource issues
- [ ] Validate all features working as expected

### Long-term (24-48 hours)
- [ ] Review deployment metrics
- [ ] Document any issues encountered
- [ ] Update runbook if process changed
- [ ] Celebrate successful deployment! 🎉

## Branching & Deployment Policy

This project uses an integration-first workflow: feature work is opened as PRs against the integration branch `integration/2025-11-sync`, CI runs there, and staging/prod deploys remain explicit and controlled.

Key rules:
- Feature PRs: open PRs with base `integration/2025-11-sync` so CI and acceptance tests run against the integration branch before any release to staging/production.
- Staging deploys: continue to be triggered by merges/pushes to the `staging` branch. Use `integration/2025-11-sync` as the validation area: once integration is green, create a release branch or merge to `staging` for a staging deploy.
- Production deploys: remain tied to `main` (or a tag). We recommend using a release tag (e.g., `v1.2.3`) or a dedicated release branch merged into `main` to trigger production deploys. This prevents accidental deploys from feature merges.
- CI: workflows should run for `integration/2025-11-sync` (pushes and PRs) as well as `staging` and `main` where appropriate.
- Deploy pipelines: do not rely on the repository default branch. Set explicit branch or tag triggers in Railway / App Engine / other CI so the deploy target is unambiguous.

Release process (recommended):
1. Finish and merge feature PRs into `integration/2025-11-sync`.
2. Run full acceptance tests on `integration/2025-11-sync`. If issues appear, fix in feature branches and re-run.
3. Create a release branch from `integration/2025-11-sync`:

```bash
git checkout integration/2025-11-sync
git pull origin integration/2025-11-sync
git checkout -b release/1.2.3
# bump version/CHANGELOG
git commit -am "release: 1.2.3"
git push origin release/1.2.3
```

4. Merge `release/1.2.3` into `staging` (or open a PR targeting `staging`) to deploy to staging for verification.
5. After final validation, merge `release/1.2.3` into `main` (or create an annotated tag `v1.2.3` on `release/1.2.3`) to trigger production deploy. Prefer annotated tags for more control:

```bash
git tag -a v1.2.3 -m "Release 1.2.3"
git push origin v1.2.3
```

6. Monitor the production deployment and follow rollback procedures if needed.

Deployment checklist additions (branching-specific):
- [ ] PRs merged to `integration/2025-11-sync` have passing CI and acceptance tests
- [ ] Release branch created from a green `integration/2025-11-sync`
- [ ] Staging validation performed from the release branch
- [ ] Production deploys triggered only from `main` or annotated tags

Notes on Railway and other CI hooks:
- If Railway is currently watching a branch for automatic deploys, make it watch only `staging` or specific release branches/tags. Avoid pointing Railway at branches used for feature work.
- Use environment-specific service tokens and secrets per environment (already enforced in workflows). When changing Railway project settings, ensure a dry-run on staging first.

## Troubleshooting

### Deployment Fails
1. Check CI/CD logs for specific error
2. Verify all secrets/environment variables set
3. Check for dependency conflicts
4. Validate database migrations
5. Review health check failures

### High Error Rate After Deployment
1. Check application logs
2. Review recent code changes
3. Check for configuration issues
4. Verify external service availability
5. Consider rollback if critical

### Performance Degradation
1. Check database query performance
2. Review resource usage (CPU, memory)
3. Check for N+1 queries or missing indexes
4. Verify caching working properly
5. Check for increased traffic patterns

### Database Connection Issues
1. Check connection pool settings
2. Verify database server health
3. Check for long-running queries
4. Review connection limits
5. Check network connectivity

## Emergency Contacts

**Deployment Owner:** [Name] - [Email/Phone]  
**Database Admin:** [Name] - [Email/Phone]  
**On-Call Engineer:** [Rotation Schedule]  
**Product Owner:** [Name] - [Email/Phone]

## Appendix

### Environment Variables (Production)
- `FLASK_ENV=production`
- `SECRET_KEY` - Session encryption key
- `DATABASE_URL` - PostgreSQL connection string
- `STRIPE_SECRET_KEY` - Payment processing
- `OPENAI_API_KEY` - Content generation
- `ADMIN_EMAILS` - Admin user emails

### Deployment Schedule
- **Preferred:** Tuesday-Thursday, 10 AM - 2 PM (low traffic)
- **Avoid:** Friday, Monday, weekends, holidays
- **Emergency:** Any time (with proper communication)

### Approval Requirements
- **Staging:** Automated on PR merge
- **Production:** Requires approval from 2 team members
- **Hotfix:** Can be expedited with 1 approval + incident ticket
