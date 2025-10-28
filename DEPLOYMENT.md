# Deployment Runbook

## Overview

This runbook describes the deployment process for Swelly, including pre-deployment checks, deployment strategies, and rollback procedures.

## Environments

### Development
- **URL:** Local (http://localhost:5001)
- **Purpose:** Local development and testing
- **Database:** SQLite (swelly.db)
- **Deploy Method:** Manual (`python app.py`)

### Staging
- **URL:** TBD (e.g., staging.swelly.app)
- **Purpose:** Pre-production testing and validation
- **Database:** PostgreSQL (staging instance)
- **Deploy Method:** CI/CD on merge to `staging` branch
- **Access:** Internal team + QA

### Production
- **URL:** TBD (e.g., swelly.app)
- **Purpose:** Live customer-facing application
- **Database:** PostgreSQL (production instance with backups)
- **Deploy Method:** CI/CD with approval gates
- **Access:** Public

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
kubectl rollout undo deployment/swelly
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
curl https://swelly.app/health

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
