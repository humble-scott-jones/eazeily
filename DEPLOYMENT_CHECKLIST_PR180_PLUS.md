# PR180+ Deployment Day Checklist

**Deployment Date**: ________________  
**Release Version**: ________________  
**Deployment Engineer**: ________________  
**On-Call Engineer**: ________________  

---

## Pre-Deployment (Complete 1 day before)

### Code Quality
- [ ] All CI checks passing
- [ ] Code reviews approved
- [ ] No merge conflicts
- [ ] Test coverage ≥ 80%
- [ ] Linting passes (`flake8`)
- [ ] No known critical bugs

### Testing
- [ ] Unit tests: 100% passing
- [ ] Integration tests: passing
- [ ] E2E tests: passing
- [ ] Manual smoke tests: completed
- [ ] Performance tests: no regressions

### Database
- [ ] Migrations tested locally
- [ ] Migrations tested on staging
- [ ] Rollback plan documented
- [ ] Production backup completed
- [ ] Validation queries prepared

### Documentation
- [ ] CHANGELOG.md updated
- [ ] API docs updated (if applicable)
- [ ] Release notes prepared
- [ ] Team notified of deployment window

### Infrastructure
- [ ] Staging environment healthy
- [ ] Staging running stable for 4+ hours
- [ ] Monitoring & alerts configured
- [ ] Health checks working
- [ ] Rollback plan reviewed

---

## Staging Deployment

### Pre-Staging
- [ ] Feature branch merged to staging branch
- [ ] CI checks passing on staging branch
- [ ] Team notified of staging deployment

### Deploy to Staging
- [ ] Deployment triggered (auto or manual)
- [ ] Deployment completed successfully
- [ ] Time: ______:______ (24h format)

### Staging Validation (Complete within 30 minutes)
- [ ] Health endpoint: `curl https://staging.togetherly.app/health` → 200 OK
- [ ] No errors in logs (first 5 min)
- [ ] Landing page loads
- [ ] User login works
- [ ] Content generation works
- [ ] Payment flow works (test mode)
- [ ] All navigation links work
- [ ] No JavaScript console errors

### Staging Metrics (Monitor for 4 hours)
- [ ] Response time p95 < 2s
- [ ] Error rate < 0.1%
- [ ] Database queries < 500ms
- [ ] CPU usage < 70%
- [ ] Memory stable (no leaks)

**Staging Sign-off**  
- [ ] Staging deployment successful and stable
- [ ] Signed off by: ________________ Time: ______:______

---

## Production Deployment

### Pre-Production Final Check
- [ ] Staging has been stable for 4+ hours
- [ ] All pre-deployment items complete
- [ ] Production database backed up
- [ ] Team on standby for deployment
- [ ] On-call engineer identified
- [ ] Rollback plan communicated

### Deploy to Production
- [ ] Create release branch: `release/1.x.x`
- [ ] Version updated in CHANGELOG
- [ ] Release branch merged to main (or manual deploy triggered)
- [ ] Deployment started: Time: ______:______
- [ ] Deployment completed: Time: ______:______

---

## Production Validation

### Immediate (0-5 minutes)
- [ ] Health check: `curl https://togetherly.app/health` → 200 OK
- [ ] No 5xx errors in logs
- [ ] Manual login test: Success
- [ ] Manual content generation test: Success
- [ ] Critical flow tested: ________________ → Success

### Short-term (5-30 minutes)
Monitor continuously and record values every 5 minutes:

| Time | Error Rate | Response Time (p95) | CPU % | Memory % | Status |
|------|------------|---------------------|-------|----------|--------|
| +5m  | _______%   | ______s             | ____% | _____%   | ___    |
| +10m | _______%   | ______s             | ____% | _____%   | ___    |
| +15m | _______%   | ______s             | ____% | _____%   | ___    |
| +20m | _______%   | ______s             | ____% | _____%   | ___    |
| +25m | _______%   | ______s             | ____% | _____%   | ___    |
| +30m | _______%   | ______s             | ____% | _____%   | ___    |

**Thresholds:**
- Error Rate: Normal < 0.1% | Warning > 0.5% | Critical > 1%
- Response Time: Normal < 2s | Warning > 3s | Critical > 5s
- CPU: Normal < 70% | Warning > 70% | Critical > 85%
- Memory: Normal < 80% | Warning > 80% | Critical > 90%

**Action Required:**
- [ ] No action needed - all metrics normal
- [ ] ⚠️ Warning threshold reached - increased monitoring
- [ ] 🚨 CRITICAL - Rollback initiated (see Rollback section)

### Extended (30 min - 4 hours)
- [ ] +1h: No new error patterns
- [ ] +2h: Database performance stable
- [ ] +3h: External integrations working (Stripe, Gemini)
- [ ] +4h: No user-reported issues

**Production Sign-off (after 4 hours)**  
- [ ] Production deployment successful and stable
- [ ] Signed off by: ________________ Time: ______:______

---

## Rollback (If Needed)

### Rollback Decision
**Rollback triggered:** Yes / No  
**Time of rollback decision:** ______:______  
**Reason for rollback:** _________________________________  
**Decision made by:** ________________

### Rollback Execution
- [ ] Rollback command executed
  ```bash
  railway deployment rollback <deployment-id> \
    --project <id> --environment production
  ```
- [ ] Rollback completed: Time: ______:______
- [ ] Health check after rollback: `curl https://togetherly.app/health` → 200 OK
- [ ] Error rate returned to normal
- [ ] Team notified of rollback

### Post-Rollback
- [ ] Incident documented
- [ ] Root cause identified: _________________________________
- [ ] Fix implemented in development
- [ ] Post-mortem scheduled

---

## Post-Deployment

### Day 1 (24 hours)
- [ ] +8h: System stable, no issues
- [ ] +12h: System stable, no issues
- [ ] +24h: System stable, no issues
- [ ] No memory leaks detected
- [ ] Background jobs running correctly
- [ ] Scheduled tasks executing on time

### Day 2 (48 hours)
- [ ] User engagement metrics normal
- [ ] Payment processing working correctly
- [ ] No increase in support tickets
- [ ] System resources stable

---

## Issues Encountered

**Document any issues during deployment:**

| Time | Issue | Severity | Action Taken | Resolved |
|------|-------|----------|--------------|----------|
|      |       |          |              |          |
|      |       |          |              |          |
|      |       |          |              |          |

---

## Lessons Learned

**What went well:**
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________

**What could be improved:**
_____________________________________________________________________
_____________________________________________________________________
_____________________________________________________________________

**Action items for next deployment:**
- [ ] _________________________________________________________________
- [ ] _________________________________________________________________
- [ ] _________________________________________________________________

---

## Final Sign-off

**Deployment Status:** Success / Rollback / Partial  
**Final Status:** _________________________________

**Sign-offs:**
- Deployment Engineer: ________________ Date: ________________
- On-Call Engineer: ________________ Date: ________________
- Team Lead: ________________ Date: ________________

---

## Quick Reference Commands

```bash
# Health check
curl https://togetherly.app/health

# View logs
railway logs --environment production --tail

# List deployments
railway deployments list --project <id> --environment production

# Rollback
railway deployment rollback <deployment-id> \
  --project <id> --environment production

# Local testing
source .venv/bin/activate
PYTHONPATH=. pytest -q
```

---

**Notes:**
Use this checklist as a living document during deployment. Check off items as you complete them, and record all relevant times and metrics for post-deployment review.

**Emergency Contact:**  
Team Slack Channel: _________________________________  
On-Call Phone: _________________________________
