# Production Deployment Checklist

Use this checklist before deploying to production to ensure all production readiness requirements are met.

## Pre-Production Checklist

### Testing & Quality Assurance

#### Code Quality
- [ ] All code reviewed and approved
- [ ] No critical or high severity bugs
- [ ] Code follows style guidelines
- [ ] All linter warnings addressed
- [ ] No TODO/FIXME comments for critical paths

#### Testing
- [ ] All unit tests pass (100%)
- [ ] All integration tests pass (100%)
- [ ] End-to-end tests pass on staging
- [ ] UI smoke tests pass
- [ ] Load testing completed with acceptable results
- [ ] Test coverage meets minimum threshold (80%)
- [ ] Manual testing completed for new features
- [ ] Cross-browser testing done (if UI changes)
- [ ] Mobile testing done (if UI changes)

#### Security
- [ ] Security scan shows no critical vulnerabilities
- [ ] Dependency vulnerabilities addressed or documented
- [ ] No secrets in code or logs
- [ ] Authentication and authorization tested
- [ ] Input validation implemented
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified
- [ ] CSRF protection enabled
- [ ] Security headers configured
- [ ] Rate limiting implemented (if needed)

### Infrastructure & Configuration

#### Environment Setup
- [ ] Production environment provisioned
- [ ] Database configured and secured
- [ ] All environment variables set
- [ ] Secrets stored securely (not in code)
- [ ] SSL/TLS certificates installed and valid
- [ ] Domain names configured
- [ ] Load balancer configured (if applicable)
- [ ] CDN configured (if applicable)

#### Database
- [ ] Database migrations tested on staging
- [ ] Database migrations are reversible
- [ ] Migration rollback plan documented
- [ ] Database backups configured and tested
- [ ] Database backup restoration tested
- [ ] Database connection pooling configured
- [ ] Database monitoring enabled
- [ ] Database alerts configured

#### Monitoring & Observability
- [ ] Application metrics collection enabled
- [ ] Log aggregation configured
- [ ] Error tracking configured (e.g., Sentry)
- [ ] Health check endpoint responding
- [ ] Uptime monitoring configured
- [ ] Performance monitoring enabled
- [ ] Distributed tracing configured (if applicable)
- [ ] Dashboards created for key metrics
- [ ] Alerts configured for critical issues
- [ ] On-call rotation established

#### Deployment
- [ ] Deployment scripts tested
- [ ] Rollback procedure documented and tested
- [ ] Blue-green or canary deployment strategy defined
- [ ] CI/CD pipeline configured
- [ ] Deployment requires approval
- [ ] Post-deployment validation script ready
- [ ] Downtime window scheduled (if needed)
- [ ] Communication plan for downtime (if needed)

### Documentation

- [ ] README updated with production info
- [ ] API documentation up to date
- [ ] Deployment runbook complete
- [ ] Incident response playbook ready
- [ ] Runbooks for common operations
- [ ] Architecture diagrams current
- [ ] Environment variables documented
- [ ] Configuration settings documented
- [ ] Release notes prepared

### Compliance & Legal

- [ ] Privacy policy reviewed
- [ ] Terms of service reviewed
- [ ] GDPR compliance verified (if applicable)
- [ ] CCPA compliance verified (if applicable)
- [ ] PCI-DSS compliance verified (for payments)
- [ ] Data retention policies defined
- [ ] Backup policies comply with regulations
- [ ] User data deletion process implemented
- [ ] Cookie consent implemented (if needed)

### Communication

- [ ] Team notified of deployment
- [ ] Stakeholders informed
- [ ] Customer communication prepared (if needed)
- [ ] Support team briefed on changes
- [ ] Status page updated
- [ ] Social media posts prepared (if needed)

### Business Readiness

- [ ] Customer support team trained
- [ ] Help documentation updated
- [ ] FAQs updated
- [ ] Support tickets reviewed and addressed
- [ ] Business metrics tracking in place
- [ ] Analytics configured
- [ ] A/B testing framework ready (if needed)

## Deployment Day Checklist

### Pre-Deployment (1 hour before)

- [ ] All team members available
- [ ] Communication channels open (#deployment, #incidents)
- [ ] Incident commander assigned
- [ ] Database backup completed
- [ ] Database backup verified
- [ ] All pre-deployment checks passed
- [ ] Traffic levels acceptable (not peak time)
- [ ] No major holidays or events

### During Deployment

- [ ] Announce deployment start
- [ ] Follow deployment runbook
- [ ] Monitor error rates
- [ ] Monitor response times
- [ ] Monitor resource utilization
- [ ] Check application logs
- [ ] Verify health checks
- [ ] Run smoke tests
- [ ] Gradually increase traffic (if canary)

### Post-Deployment (First 30 minutes)

- [ ] Health check responding correctly
- [ ] All critical endpoints working
- [ ] Database migrations completed successfully
- [ ] No spike in error rates
- [ ] Response times within acceptable range
- [ ] Resource usage normal
- [ ] No errors in application logs
- [ ] External service integrations working
- [ ] Payment processing working
- [ ] Content generation working
- [ ] User authentication working

### Post-Deployment (First 2 hours)

- [ ] Monitor metrics continuously
- [ ] Check for performance degradation
- [ ] Review error logs
- [ ] Check for memory leaks
- [ ] Monitor database performance
- [ ] Review customer feedback
- [ ] Check support tickets
- [ ] Verify all features functioning

### Post-Deployment (First 24 hours)

- [ ] Daily metrics review
- [ ] Error rate within acceptable range
- [ ] Performance within SLOs
- [ ] No unusual customer reports
- [ ] Resource utilization stable
- [ ] Database performance stable

## Rollback Checklist

If issues are detected:

### Decision to Rollback
- [ ] Issue confirmed and root cause identified
- [ ] Severity assessment completed
- [ ] Decision made to rollback (vs. forward fix)
- [ ] Team notified of rollback decision

### Rollback Execution
- [ ] Announce rollback start
- [ ] Follow rollback procedure in DEPLOYMENT.md
- [ ] Execute rollback command
- [ ] Verify rollback completed
- [ ] Run smoke tests
- [ ] Monitor metrics for improvement
- [ ] Confirm error rates normalized
- [ ] Verify all critical functionality working

### Post-Rollback
- [ ] Announce rollback completion
- [ ] Document what went wrong
- [ ] Create incident post-mortem
- [ ] Plan fix in development
- [ ] Schedule follow-up deployment
- [ ] Update runbooks based on learnings

## Sign-Off

By completing this checklist, the team confirms readiness for production deployment.

**Date:** _______________

**Deployment Lead:** _______________ (Signature)

**Engineering Lead:** _______________ (Signature)

**Product Owner:** _______________ (Signature)

## Post-Deployment Sign-Off

**Deployment Successful:** Yes / No

**Issues Encountered:** None / List below
- 
- 

**Rollback Required:** Yes / No

**Date Completed:** _______________

**Final Sign-Off:** _______________ (Signature)

---

## Notes

Use this space to document any issues, unusual circumstances, or important information about this deployment:

---

## Continuous Improvement

After each deployment, review this checklist:
- [ ] Were all items relevant?
- [ ] Should any items be added?
- [ ] Can any items be automated?
- [ ] Did we follow the process?
- [ ] What can be improved?

Update this checklist based on learnings from each deployment.
