# Deployment Guide for PR180+ - Zero-Regression Strategy

## Executive Summary

This guide provides a step-by-step deployment process for PR180 and beyond, specifically designed to prevent regressions while maintaining the application's current trajectory. The strategy emphasizes validation at every stage, gradual rollout, and quick rollback capabilities.

---

## Table of Contents

1. [Pre-Deployment Validation](#1-pre-deployment-validation)
2. [Staging Deployment](#2-staging-deployment)
3. [Production Deployment](#3-production-deployment)
4. [Post-Deployment Validation](#4-post-deployment-validation)
5. [Rollback Procedures](#5-rollback-procedures)
6. [Regression Prevention Checklist](#6-regression-prevention-checklist)

---

## 1. Pre-Deployment Validation

### 1.1 Local Development Validation

**Before pushing any code, validate locally:**

```bash
# 1. Activate virtual environment
cd /home/runner/work/eazeily/eazeily
source .venv/bin/activate

# 2. Install/update all dependencies
pip install -r requirements.txt

# 3. Run linting (must pass)
python -m flake8

# 4. Run unit tests (must pass 100%)
PYTHONPATH=. pytest -q -k "not e2e and not ui_smoke"

# 5. Start the development server
PORT=5001 FLASK_ENV=development python app.py
```

**Manual smoke testing checklist:**
- [ ] Health endpoint responds: `curl http://127.0.0.1:5001/health`
- [ ] User can access landing page: `curl http://127.0.0.1:5001/`
- [ ] Login flow works (if applicable)
- [ ] Content generation works (test with sample data)
- [ ] No console errors in browser developer tools

### 1.2 CI/CD Pipeline Validation

**Ensure all CI checks pass:**

```bash
# Check the latest CI run status for your branch
# All of these must pass before proceeding:
# - secret-scan (gitleaks)
# - tests (Python 3.10, 3.11)
# - triage-smoke (if applicable)
# - smoke (if applicable)
```

**Key CI jobs to monitor:**
- **Secret Scan**: No credentials or secrets in code
- **Unit Tests**: All tests passing across Python versions
- **Acceptance Tests**: E2E flows working correctly

### 1.3 Database Migration Validation

**If your changes include database migrations:**

```bash
# 1. Check for pending migrations
alembic current
alembic history

# 2. Create migration if needed
alembic revision -m "Description of changes"

# 3. Test migration locally (with SQLite)
alembic upgrade head

# 4. Test rollback
alembic downgrade -1
alembic upgrade head

# 5. Validate data integrity
python scripts/validate-migration.py  # if available
```

**Migration safety checklist:**
- [ ] Migration is backwards compatible
- [ ] No data loss in up/down migrations
- [ ] Indexes created concurrently (for Postgres)
- [ ] Column additions use nullable or have defaults
- [ ] No table/column drops without export plan

---

## 2. Staging Deployment

### 2.1 Pre-Staging Checklist

**Before deploying to staging:**

- [ ] All PR reviews completed and approved
- [ ] All CI checks passing on the feature branch
- [ ] Merge conflicts resolved
- [ ] CHANGELOG.md updated with changes
- [ ] No known critical bugs in the branch

### 2.2 Deploy to Staging (Railway)

**Option A: Automatic deployment via push to staging branch**

```bash
# 1. Ensure you're on the correct branch
git checkout your-feature-branch
git pull origin your-feature-branch

# 2. Merge to staging branch (or create PR)
git checkout staging
git pull origin staging
git merge your-feature-branch

# 3. Push to trigger automatic deployment
git push origin staging
```

**Option B: Manual deployment via GitHub Actions**

1. Go to GitHub Actions → "Deploy (Railway)"
2. Click "Run workflow"
3. Select environment: `staging`
4. Click "Run workflow" button

**Monitor the deployment:**

```bash
# Watch GitHub Actions for deployment status
# Or use Railway CLI:
railway deployments list --project <project-id> --environment staging
```

### 2.3 Staging Validation

**Immediately after staging deployment:**

```bash
# 1. Health check (should return 200)
curl https://staging.togetherly.app/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "services": { "stripe": "available", "gemini": "available" }
# }

# 2. Check application logs for errors
# Via Railway dashboard or CLI:
railway logs --environment staging

# 3. Run staging smoke tests
RUN_UI_SMOKE=1 STAGING_URL=https://staging.togetherly.app pytest tests/
```

**Manual testing on staging:**
- [ ] Landing page loads correctly
- [ ] User registration/login works
- [ ] Dashboard loads with correct data
- [ ] Content generation works (all platforms)
- [ ] Payment flow works (use Stripe test mode)
- [ ] Copy-to-clipboard functionality works
- [ ] All navigation links work
- [ ] No JavaScript console errors

### 2.4 Staging Performance Check

**Monitor key metrics for 15-30 minutes:**

- **Response Time**: p95 should be < 2 seconds
- **Error Rate**: Should be < 0.1%
- **Database Queries**: No slow queries (> 500ms)
- **Memory Usage**: Stable, no leaks
- **CPU Usage**: < 70% under normal load

**If any metric is outside acceptable range, STOP and rollback staging.**

---

## 3. Production Deployment

### 3.1 Pre-Production Checklist

**CRITICAL: Complete ALL items before production deployment:**

#### Code Quality
- [ ] All CI checks pass (tests, linting, security scans)
- [ ] Code review approved by at least one team member
- [ ] No known critical or high-severity bugs
- [ ] Test coverage meets minimum threshold (80%)

#### Testing
- [ ] Unit tests pass (100%)
- [ ] Integration tests pass on staging
- [ ] E2E tests pass on staging
- [ ] Manual smoke testing completed on staging
- [ ] Performance tests show no regressions
- [ ] Staging has been running stable for at least 4 hours

#### Security
- [ ] Dependency vulnerability scan shows no critical issues
- [ ] Secrets rotated if needed
- [ ] Security headers configured
- [ ] HTTPS enforced
- [ ] No sensitive data in logs

#### Database
- [ ] Database migrations tested on staging
- [ ] Migration rollback plan documented
- [ ] Production database backup completed
- [ ] Migration is backwards compatible OR downtime scheduled
- [ ] Data validation queries prepared

#### Documentation
- [ ] CHANGELOG.md updated
- [ ] API documentation updated if endpoints changed
- [ ] Release notes prepared
- [ ] Runbook updated if deployment process changed

#### Monitoring
- [ ] Alerts configured for new features
- [ ] Dashboards updated with new metrics
- [ ] Log aggregation verified
- [ ] Health checks validate new functionality

#### Communication
- [ ] Team notified of deployment window
- [ ] Stakeholders informed of expected changes
- [ ] On-call engineer identified
- [ ] Rollback plan communicated to team

### 3.2 Deploy to Production (Railway)

**Recommended: Blue-Green Deployment Strategy**

The Railway platform supports blue-green deployments through its environment system. However, for simpler deployments, follow this process:

**Step 1: Create a release branch**

```bash
# 1. Checkout the integration branch
git checkout integration/2025-11-sync
git pull origin integration/2025-11-sync

# 2. Create release branch
git checkout -b release/1.x.x

# 3. Update version and changelog
# Edit CHANGELOG.md, add version bump if applicable
git commit -am "release: 1.x.x"
git push origin release/1.x.x
```

**Step 2: Deploy to production**

```bash
# Option A: Merge release branch to main
git checkout main
git pull origin main
git merge release/1.x.x
git push origin main
# This triggers automatic production deployment

# Option B: Manual deployment via GitHub Actions
# Go to GitHub Actions → "Deploy (Railway)" → Run workflow
# Select environment: production
```

**Step 3: Monitor deployment**

```bash
# Watch Railway deployment
railway deployments list --project <project-id> --environment production

# Check logs for errors
railway logs --environment production --tail
```

### 3.3 Production Validation (Critical - First 30 Minutes)

**Immediate checks (0-5 minutes):**

```bash
# 1. Health endpoint
curl https://togetherly.app/health
# Must return: {"status": "healthy"}

# 2. Check error rates in logs
# Look for 5xx errors, exceptions

# 3. Validate critical user flows manually
# - User login
# - Content generation
# - Payment (if applicable)
```

**Short-term monitoring (5-30 minutes):**

Monitor these metrics continuously:

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| Error Rate | < 0.1% | > 0.5% | > 1% |
| Response Time (p95) | < 2s | > 3s | > 5s |
| Database Connections | < 80% | > 80% | > 90% |
| CPU Usage | < 70% | > 70% | > 85% |
| Memory Usage | < 80% | > 80% | > 90% |

**If ANY metric reaches WARNING level: Increase monitoring frequency**
**If ANY metric reaches CRITICAL level: ROLLBACK IMMEDIATELY**

---

## 4. Post-Deployment Validation

### 4.1 Extended Monitoring (30 minutes - 4 hours)

**Continue monitoring:**
- [ ] Error rates remain normal
- [ ] No new error patterns in logs
- [ ] Database performance stable
- [ ] External service integrations working (Stripe, Gemini)
- [ ] User-reported issues (support tickets, feedback forms)

### 4.2 Feature Validation

**For each new feature in the deployment:**
- [ ] Feature works as expected in production
- [ ] No unintended side effects on existing features
- [ ] Performance is acceptable under real load
- [ ] Analytics/tracking is working if applicable

### 4.3 Long-term Monitoring (4-48 hours)

**Day 1 checks:**
- [ ] No memory leaks detected
- [ ] No database connection pool exhaustion
- [ ] Background jobs running correctly
- [ ] Scheduled tasks executing on time
- [ ] External API integrations stable

**Day 2 checks:**
- [ ] User engagement metrics normal or improved
- [ ] Payment processing working correctly
- [ ] No increase in support tickets
- [ ] System resources stable

---

## 5. Rollback Procedures

### 5.1 When to Rollback

**Rollback immediately if:**
- Error rate > 1%
- Response time p95 > 5 seconds
- Critical functionality broken
- Security vulnerability introduced
- Database corruption detected
- Payment processing failing
- More than 3 user-reported critical issues

### 5.2 Rollback Process (Railway)

**Quick rollback (< 5 minutes):**

```bash
# 1. List recent deployments
railway deployments list --project <project-id> --environment production

# 2. Identify the previous stable deployment ID
# Look for the deployment before the current one

# 3. Rollback to that deployment
railway deployment rollback <deployment-id> \
  --project <project-id> \
  --environment production

# 4. Verify rollback successful
curl https://togetherly.app/health
```

**Rollback via GitHub Actions:**

```bash
# 1. Revert the merge commit on main
git checkout main
git revert -m 1 HEAD
git push origin main

# This triggers automatic deployment of the reverted code
```

### 5.3 Post-Rollback Actions

**After rolling back:**
- [ ] Notify team via incident channel
- [ ] Verify error rate returns to normal
- [ ] Document what went wrong
- [ ] Create incident post-mortem
- [ ] Fix issue in development
- [ ] Repeat deployment process with fix

### 5.4 Database Rollback

**If database migration needs rollback:**

```bash
# If migration has down migration
alembic downgrade -1

# If no down migration, restore from backup
# Contact DBA or use Railway backup restore
```

---

## 6. Regression Prevention Checklist

### 6.1 Code-Level Prevention

- [ ] **Comprehensive test coverage**: Aim for 80%+ coverage
- [ ] **Integration tests**: Test interactions between components
- [ ] **E2E tests**: Validate critical user journeys
- [ ] **Backward compatibility**: Ensure APIs remain compatible
- [ ] **Feature flags**: Use flags for risky changes
- [ ] **Code review**: At least one approval required
- [ ] **Static analysis**: Run linters and type checkers

### 6.2 Process-Level Prevention

- [ ] **Staging matches production**: Same infrastructure, config
- [ ] **Soak time on staging**: Run for 4+ hours before production
- [ ] **Gradual rollout**: Consider canary or blue-green deployments
- [ ] **Deployment windows**: Deploy during low-traffic periods
- [ ] **Avoid Friday deploys**: Give time to monitor before weekend
- [ ] **Monitoring in place**: Alerts configured before deployment
- [ ] **Runbook ready**: Team knows how to rollback

### 6.3 Testing Strategy

**Test pyramid approach:**

```
        /\
       /E2E\          <- Few E2E tests (critical paths)
      /------\
     /  API   \       <- More API/integration tests
    /----------\
   /   UNIT     \     <- Many unit tests (fast, isolated)
  /--------------\
```

**Required tests for each PR:**
- Unit tests for new functions/classes
- Integration tests for new endpoints
- E2E tests for new user flows
- Regression tests for bug fixes

### 6.4 Monitoring & Alerting

**Set up alerts for:**
- Error rate > 1% (critical)
- Response time p95 > 5s (critical)
- Database connection failures (critical)
- Memory usage > 90% (warning)
- CPU usage > 85% (warning)
- Disk space < 20% (warning)

---

## 7. Quick Reference

### Command Cheat Sheet

```bash
# Local testing
source .venv/bin/activate
PYTHONPATH=. pytest -q
PORT=5001 python app.py

# Deploy to staging (automatic)
git checkout staging
git merge your-feature-branch
git push origin staging

# Deploy to production (automatic)
git checkout main
git merge release/1.x.x
git push origin main

# Manual deploy via workflow_dispatch
# Use GitHub UI: Actions → Deploy (Railway) → Run workflow

# Check deployment
railway deployments list --project <id> --environment <env>

# View logs
railway logs --environment production --tail

# Rollback
railway deployment rollback <deployment-id> \
  --project <id> --environment production

# Health check
curl https://togetherly.app/health
```

### Decision Tree

```
Is the feature ready?
├─ No → Continue development
└─ Yes → Run local tests
    ├─ Failed → Fix issues
    └─ Passed → Push to feature branch
        └─ CI passes?
            ├─ No → Fix CI issues
            └─ Yes → Merge to staging
                └─ Staging stable for 4h?
                    ├─ No → Investigate/rollback
                    └─ Yes → Create release branch
                        └─ Deploy to production
                            └─ Monitor for 30m
                                ├─ Issues detected → ROLLBACK
                                └─ All good → Continue monitoring
```

---

## 8. Special Considerations for PR180+

### 8.1 What's New Beyond PR180

Based on the repository analysis, the application is heading toward:
- **Onboarding improvements**: Website-first scraping, social rhythm samples
- **Team workflow features**: Team management, draft collaboration
- **Postgres migration**: Moving from SQLite to Postgres
- **Enhanced AI**: Google Gemini integration for content generation
- **Payment integration**: Stripe subscription management

### 8.2 Key Areas to Test

For PR180+ deployments, ensure these areas are thoroughly tested:

1. **Database compatibility**
   - Postgres connection works
   - Migrations run cleanly
   - Query performance acceptable

2. **AI content generation**
   - Gemini API integration works
   - Fallback to local generator works
   - Content quality maintained

3. **User onboarding flow**
   - Website scraping works
   - Social rhythm samples display
   - User wizard completes successfully

4. **Team features (if applicable)**
   - Team creation/management
   - Draft sharing
   - Permission boundaries

5. **Payment flow**
   - Stripe integration works
   - Webhook handling correct
   - Subscription status updates

### 8.3 Migration Considerations

**If moving from SQLite to Postgres:**

```bash
# 1. Backup SQLite database
cp togetherly.db togetherly.db.backup

# 2. Export data (if needed)
# Use custom export script or pg_dump equivalent

# 3. Test on staging first
# Deploy to staging, verify data integrity

# 4. Plan downtime or use live migration tools
# Consider zero-downtime migration strategies
```

---

## 9. Troubleshooting Common Issues

### Deployment Fails

**Symptoms**: Railway deployment fails, service won't start

**Debug steps:**
```bash
# 1. Check deployment logs
railway logs --environment <env> --deployment <deployment-id>

# 2. Common issues:
# - Missing environment variables
# - Database connection failed
# - Build errors (dependencies)
# - Port binding issues

# 3. Verify secrets
# Check GitHub Secrets and Railway environment variables
```

### High Error Rate After Deployment

**Symptoms**: Error rate > 1%, 5xx errors in logs

**Debug steps:**
```bash
# 1. Check application logs
railway logs --environment production --tail

# 2. Look for:
# - Database connection errors
# - External API failures (Stripe, Gemini)
# - Missing configuration
# - Code exceptions

# 3. Rollback if critical
railway deployment rollback <previous-deployment-id>
```

### Performance Degradation

**Symptoms**: Slow response times, high CPU/memory

**Debug steps:**
```bash
# 1. Check database queries
# Look for slow queries, N+1 issues

# 2. Check external API latency
# Gemini, Stripe response times

# 3. Profile the application
# Use Flask profiling middleware

# 4. Scale up resources temporarily
# Via Railway dashboard, increase RAM/CPU
```

---

## 10. Emergency Contacts & Resources

### Key Documentation
- **Deployment runbook**: `/DEPLOYMENT.md`
- **Production checklist**: `/PRODUCTION_CHECKLIST.md`
- **Launch checklist**: `/LAUNCH_CHECKLIST.md`
- **Monitoring guide**: `/MONITORING.md`
- **Security guide**: `/SECURITY.md`
- **Incident response**: `/INCIDENT_RESPONSE.md`

### Railway Resources
- **Dashboard**: https://railway.app/dashboard
- **Docs**: https://docs.railway.app/
- **Status**: https://status.railway.app/

### CI/CD Resources
- **GitHub Actions**: `.github/workflows/`
- **Railway deployment workflow**: `.github/workflows/deploy-railway.yml`
- **CI workflow**: `.github/workflows/ci.yml`

---

## Summary

This deployment guide provides a comprehensive, regression-free path for deploying PR180 and beyond. The key principles are:

1. **Validate at every stage**: Local → CI → Staging → Production
2. **Monitor continuously**: Especially first 30 minutes post-deployment
3. **Rollback quickly**: Don't hesitate if metrics are concerning
4. **Test thoroughly**: Unit, integration, E2E, and manual testing
5. **Document everything**: Changes, issues, rollbacks, learnings

By following this guide, you can confidently deploy new features while maintaining the application's stability and trajectory.

**Remember**: It's better to delay a deployment than to rush and cause an outage. When in doubt, rollback and investigate.
