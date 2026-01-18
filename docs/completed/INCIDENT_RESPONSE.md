# Incident Response Playbook

## Overview

This playbook provides step-by-step procedures for responding to production incidents, including detection, triage, resolution, and post-incident activities.

## Incident Severity Levels

### SEV-1 (Critical)
**Impact:** Complete service outage or data loss  
**Response Time:** Immediate (< 5 minutes)  
**Examples:**
- Application completely down
- Database unavailable
- Payment processing completely broken
- Data breach or security incident
- Widespread data corruption

**Actions:**
- Page on-call engineer immediately
- Notify incident commander
- Create incident channel
- Update status page

### SEV-2 (High)
**Impact:** Major functionality broken, affects many users  
**Response Time:** < 15 minutes  
**Examples:**
- Critical feature not working (content generation, auth)
- Severe performance degradation (> 5s response times)
- Elevated error rate (> 5%)
- Payment processing partially broken
- Database performance issues

**Actions:**
- Alert on-call engineer
- Create incident ticket
- Notify team via Slack

### SEV-3 (Medium)
**Impact:** Minor functionality issues, affects some users  
**Response Time:** < 1 hour  
**Examples:**
- Non-critical feature broken
- Moderate performance degradation
- Elevated error rate (1-5%)
- Third-party service degradation

**Actions:**
- Create ticket
- Assign to on-call engineer
- Fix during business hours

### SEV-4 (Low)
**Impact:** Minor issues, minimal user impact  
**Response Time:** < 24 hours  
**Examples:**
- UI glitches
- Minor bugs
- Non-customer-facing issues

**Actions:**
- Create bug ticket
- Address in normal workflow

## Incident Response Process

### 1. Detection and Alert

**How Incidents are Detected:**
- Automated monitoring alerts
- User reports
- Customer support tickets
- Internal team notices issue

**First Steps:**
1. Acknowledge alert in monitoring system
2. Check status page and dashboards
3. Confirm incident is real (not false positive)
4. Determine severity level

### 2. Initial Response (First 5 Minutes)

**For SEV-1/SEV-2:**
1. **Notify team:**
   ```
   #incidents Slack channel:
   "🚨 SEV-X INCIDENT: [Brief description]
   Status: Investigating
   Commander: [Name]
   Time: [UTC timestamp]
   Link: [Incident ticket/channel]"
   ```

2. **Create incident channel:**
   - Slack: `#incident-YYYY-MM-DD-description`
   - Invite key responders
   - Pin important updates

3. **Assign roles:**
   - **Incident Commander:** Coordinates response
   - **Technical Lead:** Investigates and implements fix
   - **Communications Lead:** Updates stakeholders

4. **Update status page:**
   - Acknowledge incident
   - Set status to "Investigating"
   - Provide initial information

### 3. Investigation and Diagnosis

**Information to Gather:**
- When did the incident start?
- What changed recently? (deployments, config changes)
- What are the symptoms?
- How many users are affected?
- What's the business impact?

**Investigation Steps:**
1. **Check recent changes:**
   ```bash
   # Recent deployments
   git log --oneline -10
   
   # Recent config changes
   kubectl get events --sort-by='.lastTimestamp'
   ```

2. **Review logs:**
   ```bash
   # Application errors
   grep "ERROR\|CRITICAL" logs/app.log | tail -100
   
   # Database errors
   grep "ERROR" logs/db.log | tail -50
   ```

3. **Check metrics:**
   - Error rate
   - Response time
   - Resource usage (CPU, memory, disk)
   - Database performance
   - External service status

4. **Reproduce issue:**
   - Try to reproduce in staging
   - Test affected functionality
   - Narrow down root cause

### 4. Mitigation and Resolution

**Mitigation Options (in order of preference):**

1. **Quick Fix:**
   - Fix the bug and deploy
   - Apply configuration change
   - Restart service if safe

2. **Rollback:**
   - Roll back to last known good version
   - Revert configuration change
   - See DEPLOYMENT.md for rollback procedures

3. **Workaround:**
   - Disable problematic feature via feature flag
   - Route traffic around failing component
   - Scale resources if capacity issue

4. **Temporary Fix:**
   - Apply band-aid solution
   - Plan proper fix for later

**Resolution Steps:**
1. Implement chosen mitigation
2. Verify fix in staging (if time permits)
3. Deploy fix to production
4. Monitor metrics for improvement
5. Confirm resolution with affected users
6. Verify error rates return to normal

### 5. Communication

**Internal Communication:**
- Update incident channel every 15-30 minutes
- Include: What we know, what we're doing, ETA
- Keep team informed of progress

**External Communication (if customer-facing):**
- Update status page within 15 minutes
- Post updates every 30 minutes
- Be honest and transparent
- Provide workarounds if available

**Example Status Page Update:**
```
[14:30 UTC] Investigating: We are aware of issues with content 
generation and are actively investigating. Users may experience 
delays or failures when generating content.

[14:45 UTC] Update: We have identified the issue as a 
third-party API timeout and are implementing a fix.

[15:00 UTC] Resolved: The issue has been resolved. Content 
generation is functioning normally.
```

### 6. Resolution and Closure

**When incident is resolved:**
1. Confirm all symptoms are gone
2. Verify metrics return to normal
3. Monitor for 30 minutes to ensure stability
4. Update status page to "Resolved"
5. Post resolution message in incident channel
6. Thank responders

**Resolution Message:**
```
✅ RESOLVED: [Brief description]
Root cause: [Summary]
Resolution: [What was done]
Duration: [Time from detection to resolution]
Affected users: [Estimate]
Post-mortem: [Link to be added]
```

### 7. Post-Incident Activities

**Within 24 hours:**
- [ ] Schedule post-mortem meeting
- [ ] Create post-mortem document
- [ ] Gather incident timeline
- [ ] Collect relevant logs and metrics

**Within 48 hours:**
- [ ] Complete post-mortem document
- [ ] Identify root cause
- [ ] List action items to prevent recurrence
- [ ] Share with team and stakeholders

**Within 1 week:**
- [ ] Complete action items (or schedule them)
- [ ] Update runbooks if needed
- [ ] Improve monitoring/alerts if gaps found
- [ ] Archive incident channel

## Common Incident Scenarios

### High Error Rate

**Symptoms:**
- Error rate > 1% or sudden spike
- Users reporting failures
- Alerts firing

**Possible Causes:**
- Bad deployment
- Database issues
- External API failures
- Resource exhaustion

**Troubleshooting:**
```bash
# Check error logs
grep "ERROR" logs/app.log | tail -100

# Check recent deployments
git log --oneline -5

# Check external services
curl https://status.stripe.com
curl https://status.gemini.com

# Check database
psql -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"
```

**Resolution:**
- If bad deployment: Rollback
- If external API: Wait or implement circuit breaker
- If database: Optimize queries or scale
- If resources: Scale up or optimize

### Slow Performance

**Symptoms:**
- Response time p95 > 3 seconds
- Users reporting slowness
- Timeouts

**Possible Causes:**
- Slow database queries
- Resource constraints (CPU, memory)
- External API latency
- Too much traffic

**Troubleshooting:**
```bash
# Check response times
# (check monitoring dashboard)

# Check slow queries
psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# Check resource usage
top
free -h
df -h

# Check database connection pool
psql -c "SELECT count(*) FROM pg_stat_activity;"
```

**Resolution:**
- Optimize slow queries (add indexes)
- Scale resources (CPU, memory)
- Increase database connection pool
- Cache frequently accessed data
- Implement rate limiting

### Database Connection Issues

**Symptoms:**
- "Too many connections" errors
- Connection timeouts
- Database unavailable

**Possible Causes:**
- Connection pool exhausted
- Database server overloaded
- Connection leaks
- Network issues

**Troubleshooting:**
```bash
# Check active connections
psql -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check long-running queries
psql -c "SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"

# Check connection pool stats
# (check application metrics)
```

**Resolution:**
- Kill long-running queries
- Increase connection pool size
- Fix connection leaks in code
- Scale database if needed
- Restart application to reset connections

### Payment Processing Failures

**Symptoms:**
- Payment failures spike
- Users can't subscribe
- Webhook processing failures

**Possible Causes:**
- Stripe API issues
- Webhook secret mismatch
- Database issues
- Code bug in payment flow

**Troubleshooting:**
```bash
# Check Stripe status
curl https://status.stripe.com/api/v2/status.json

# Check webhook logs
grep "webhook" logs/app.log | tail -50

# Check payment errors
grep "payment.*ERROR" logs/app.log | tail -50

# Verify webhook secret
echo $STRIPE_WEBHOOK_SECRET
```

**Resolution:**
- If Stripe issue: Wait for resolution, communicate to users
- If webhook secret: Update secret in environment
- If database: Fix database issue
- If code bug: Hotfix and deploy

### Service Completely Down

**Symptoms:**
- Health check fails
- All requests return 503
- Application not responding

**Possible Causes:**
- Application crash
- Deployment failure
- Infrastructure issue
- Database unavailable

**Troubleshooting:**
```bash
# Check application status
curl https://togetherly.app/health

# Check application logs
tail -100 logs/app.log

# Check container/process status
ps aux | grep python
# or
kubectl get pods

# Check infrastructure
# (cloud provider console)
```

**Resolution:**
- Restart application
- Rollback deployment
- Fix infrastructure issue
- Restore database connection

### External API Degradation

**Symptoms:**
- Content generation fails
- Payment processing slow
- Third-party service errors

**Possible Causes:**
- OpenAI rate limits
- Stripe API issues
- Network connectivity

**Troubleshooting:**
```bash
# Check external service status
curl https://status.gemini.com
curl https://status.stripe.com

# Check API error rate
grep "gemini.*ERROR\|stripe.*ERROR" logs/app.log | tail -50

# Test API connectivity
curl -X POST https://api.gemini.com/v1/... \
  -H "Authorization: Bearer $GEMINI_API_KEY"
```

**Resolution:**
- Implement circuit breaker
- Add retry logic with exponential backoff
- Queue requests for later processing
- Communicate to users about degradation
- Contact vendor support if needed

## Service Level Objectives (SLOs)

### Availability SLO
**Target:** 99.9% uptime (43 minutes downtime per month)  
**Measurement:** Health check success rate  
**Error Budget:** 0.1% (43 minutes per month)

**If error budget exhausted:**
- Freeze non-critical deployments
- Focus on reliability improvements
- Review incidents and fix root causes

### Performance SLO
**Target:** p95 response time < 2 seconds  
**Measurement:** HTTP request duration histogram  
**Error Budget:** 5% of requests may exceed threshold

**If error budget exhausted:**
- Prioritize performance optimizations
- Review slow queries and endpoints
- Consider capacity upgrades

### Success Rate SLO
**Target:** 99.5% successful requests (< 0.5% error rate)  
**Measurement:** HTTP 5xx / total requests  
**Error Budget:** 0.5%

**If error budget exhausted:**
- Increase test coverage
- Add more defensive code
- Improve error handling

## Error Budget Policy

**When error budget is healthy (> 50% remaining):**
- Normal development velocity
- Accept calculated risks
- Deploy features confidently

**When error budget is low (10-50% remaining):**
- Increase caution on deployments
- Require more testing
- Focus on stability

**When error budget is exhausted (< 10% remaining):**
- Feature freeze (except critical fixes)
- Focus on reliability
- Root cause analysis of recent incidents
- No risky changes until budget recovers

## Escalation

### When to Escalate

Escalate to next level if:
- Incident severity higher than responder can handle
- Fix taking longer than expected
- Need additional expertise
- Incident affecting critical business function

### Escalation Path

1. **On-call Engineer**
2. **Engineering Lead**
3. **Engineering Manager**
4. **CTO**
5. **CEO** (for critical incidents with business impact)

### Contact Information

**On-call Rotation:** [Link to PagerDuty/Opsgenie schedule]

**Key Contacts:**
- Engineering Lead: [Name] - [Phone/Email]
- Engineering Manager: [Name] - [Phone/Email]
- Product Manager: [Name] - [Phone/Email]
- Customer Support Lead: [Name] - [Phone/Email]

## Post-Mortem Template

Use this template for post-incident reviews:

---

### Incident Post-Mortem: [Title]

**Date:** YYYY-MM-DD  
**Severity:** SEV-X  
**Duration:** X hours Y minutes  
**Incident Commander:** [Name]

#### Summary
Brief description of what happened.

#### Impact
- **Users affected:** [Number/percentage]
- **Duration:** [Time]
- **Business impact:** [Revenue, reputation, etc.]
- **Services affected:** [List]

#### Timeline (UTC)
- HH:MM - Incident detected
- HH:MM - Team notified
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Resolution confirmed

#### Root Cause
Detailed explanation of what caused the incident.

#### Resolution
What was done to resolve the incident.

#### What Went Well
- Quick detection via monitoring
- Effective team coordination
- Fast rollback procedure

#### What Went Wrong
- Slow to identify root cause
- Insufficient test coverage
- Alert threshold too high

#### Action Items
- [ ] [ACTION-1] Improve test coverage for X - [Owner] - [Due date]
- [ ] [ACTION-2] Add monitoring for Y - [Owner] - [Due date]
- [ ] [ACTION-3] Update runbook for Z - [Owner] - [Due date]

#### Lessons Learned
- Always test migrations on staging data
- Monitor X metric to catch similar issues earlier
- Need better error messages for debugging

---

## Incident Response Checklist

**Detection (< 5 min):**
- [ ] Acknowledge alert
- [ ] Verify incident is real
- [ ] Determine severity
- [ ] Check recent changes

**Initial Response (< 5 min for SEV-1/2):**
- [ ] Notify team in #incidents
- [ ] Create incident channel
- [ ] Assign incident commander
- [ ] Update status page (if customer-facing)

**Investigation:**
- [ ] Gather information (logs, metrics, timeline)
- [ ] Identify affected users/services
- [ ] Determine root cause
- [ ] Check for similar issues in the past

**Mitigation:**
- [ ] Implement fix, rollback, or workaround
- [ ] Verify fix in staging (if time permits)
- [ ] Deploy to production
- [ ] Monitor metrics for improvement

**Communication:**
- [ ] Update incident channel regularly
- [ ] Update status page (if customer-facing)
- [ ] Notify affected users
- [ ] Update stakeholders

**Resolution:**
- [ ] Confirm symptoms are gone
- [ ] Monitor for stability (30 minutes)
- [ ] Update status page to "Resolved"
- [ ] Post resolution message
- [ ] Thank responders

**Post-Incident:**
- [ ] Schedule post-mortem (within 24 hours)
- [ ] Write post-mortem document (within 48 hours)
- [ ] Assign action items
- [ ] Complete action items (within 1 week)
- [ ] Update runbooks/alerts as needed

## Prevention

**Best practices to prevent incidents:**
- Comprehensive testing before deployment
- Gradual rollout strategies (canary, blue-green)
- Monitoring and alerting for all critical paths
- Regular load and performance testing
- Runbook maintenance and team training
- Post-mortem action items completion
- Chaos engineering to test resilience

## Related Documents

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures and rollback
- [MONITORING.md](./MONITORING.md) - Monitoring and alerting setup
- [TESTING.md](./TESTING.md) - Testing strategy and procedures
- Status Page: [URL]
- Incident Archive: [URL]
- On-call Schedule: [URL]
