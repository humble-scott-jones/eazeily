# Deployment Documentation for PR180+

## Overview

This directory contains comprehensive deployment documentation for deploying PR180 and beyond without introducing regressions. The documentation is designed to be practical, actionable, and focused on preventing issues before they reach production.

---

## 📚 Documentation Files

### Primary Documents

1. **[DEPLOYMENT_GUIDE_PR180_PLUS.md](./DEPLOYMENT_GUIDE_PR180_PLUS.md)**
   - **Purpose**: Complete step-by-step deployment guide
   - **Audience**: DevOps engineers, release managers
   - **Length**: ~500 lines
   - **Use when**: Planning or executing any deployment
   - **Key sections**:
     - Pre-deployment validation
     - Staging deployment process
     - Production deployment process
     - Post-deployment validation
     - Rollback procedures
     - Regression prevention strategies

2. **[DEPLOYMENT_CHECKLIST_PR180_PLUS.md](./DEPLOYMENT_CHECKLIST_PR180_PLUS.md)**
   - **Purpose**: Printable checklist for deployment day
   - **Audience**: Person executing the deployment
   - **Length**: ~200 lines
   - **Use when**: During active deployment
   - **Key sections**:
     - Pre-deployment items
     - Staging validation
     - Production validation
     - Metrics tracking table
     - Rollback decision tree
     - Post-deployment monitoring

3. **[DEPLOYMENT_FLOW_DIAGRAM.md](./DEPLOYMENT_FLOW_DIAGRAM.md)**
   - **Purpose**: Visual representation of deployment process
   - **Audience**: All team members
   - **Length**: ~400 lines
   - **Use when**: Understanding the deployment flow
   - **Key sections**:
     - Visual deployment pipeline
     - Rollback decision tree
     - Deployment timeline
     - Monitoring dashboard layout
     - Quick decision guide

4. **[scripts/pre_deployment_check.sh](./scripts/pre_deployment_check.sh)**
   - **Purpose**: Automated pre-deployment validation
   - **Audience**: Developers, DevOps engineers
   - **Type**: Bash script (executable)
   - **Use when**: Before any deployment to staging or production
   - **Checks performed**:
     - Git status and branch validation
     - Merge conflict detection
     - Python environment setup
     - Dependency verification
     - Environment variable checks
     - Linting (flake8)
     - Unit test execution
     - Database migration validation
     - Security checks
     - Documentation updates

### Supporting Documents

5. **[DEPLOYMENT.md](./DEPLOYMENT.md)** (Original)
   - Comprehensive deployment runbook
   - Railway and App Engine deployment details
   - Environment configuration
   - Database migration procedures
   - Branching policy

6. **[PRODUCTION_CHECKLIST.md](./PRODUCTION_CHECKLIST.md)**
   - Production readiness items
   - Security baseline
   - Monitoring setup
   - Infrastructure requirements

7. **[LAUNCH_CHECKLIST.md](./LAUNCH_CHECKLIST.md)**
   - Complete launch preparation checklist
   - Must-have vs. nice-to-have items
   - GitHub issue templates
   - Sprint planning guidance

---

## 🚀 Quick Start

### For Your First Deployment

1. **Read the guide**:
   ```bash
   cat DEPLOYMENT_GUIDE_PR180_PLUS.md | less
   ```

2. **Run pre-deployment checks**:
   ```bash
   ./scripts/pre_deployment_check.sh staging
   ```

3. **Print the checklist**:
   ```bash
   # Print to PDF or paper for deployment day
   cat DEPLOYMENT_CHECKLIST_PR180_PLUS.md
   ```

4. **Review the flow diagram**:
   ```bash
   cat DEPLOYMENT_FLOW_DIAGRAM.md | less
   ```

5. **Execute deployment** (following the guide)

---

## 📋 Deployment Process Summary

### Three-Phase Approach

```
Development → Staging (validate 4h) → Production (monitor 48h)
```

### Key Timeframes

- **Local validation**: 15-30 minutes
- **Staging deployment**: 5-10 minutes
- **Staging validation**: 4 hours minimum
- **Production deployment**: 5-10 minutes
- **Critical monitoring**: 30 minutes (every 5 min checks)
- **Extended monitoring**: 48 hours
- **Rollback time**: < 5 minutes

---

## 🎯 Zero-Regression Strategy

### Core Principles

1. **Validate at every stage**: Local → CI → Staging → Production
2. **Monitor continuously**: Especially first 30 minutes post-deployment
3. **Rollback quickly**: Don't hesitate if metrics are concerning
4. **Test thoroughly**: Unit, integration, E2E, and manual testing
5. **Document everything**: Changes, issues, rollbacks, learnings

### Regression Prevention Checklist

- [ ] All tests passing (unit, integration, E2E)
- [ ] Code reviewed and approved
- [ ] Staging stable for 4+ hours
- [ ] Database migrations tested
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Team notified
- [ ] Documentation updated

---

## 🛠️ Tools and Scripts

### Pre-Deployment Validation Script

Run before any deployment:

```bash
# For staging deployment
./scripts/pre_deployment_check.sh staging

# For production deployment
./scripts/pre_deployment_check.sh production
```

The script validates:
- ✅ Git status and branch
- ✅ Python environment
- ✅ Dependencies
- ✅ Environment variables
- ✅ Linting
- ✅ Unit tests
- ✅ Database migrations
- ✅ Security checks
- ✅ Documentation

### Manual Commands

```bash
# Health check
curl https://togetherly.app/health

# View Railway logs
railway logs --environment production --tail

# List deployments
railway deployments list --project <id> --environment production

# Rollback
railway deployment rollback <deployment-id> \
  --project <id> --environment production
```

---

## 📊 Monitoring Thresholds

### Normal Operating Range

| Metric | Normal | Warning | Critical | Action |
|--------|--------|---------|----------|--------|
| Error Rate | < 0.1% | 0.1-0.5% | > 0.5% | Rollback at 1% |
| Response Time (p95) | < 2s | 2-3s | > 3s | Rollback at 5s |
| CPU Usage | < 70% | 70-85% | > 85% | Scale up |
| Memory Usage | < 80% | 80-90% | > 90% | Investigate |
| Database Connections | < 80% | 80-90% | > 90% | Scale DB |

### When to Rollback Immediately

- ❌ Error rate > 1%
- ❌ Response time p95 > 5 seconds
- ❌ Critical functionality broken
- ❌ Security vulnerability introduced
- ❌ Database corruption detected
- ❌ Payment processing failing
- ❌ > 3 user-reported critical issues

---

## 🔄 Deployment Workflow

### Staging Deployment

```bash
# 1. Merge feature to staging
git checkout staging
git merge feature-branch
git push origin staging

# 2. Automatic deployment triggered
# Monitor: https://github.com/humble-scott-jones/eazeily/actions

# 3. Validate staging
curl https://staging.togetherly.app/health

# 4. Monitor for 4 hours minimum
# Check metrics, logs, manual testing

# 5. Sign off when stable
```

### Production Deployment

```bash
# 1. Create release branch
git checkout integration/2025-11-sync
git checkout -b release/1.x.x

# 2. Update CHANGELOG
# Edit and commit

# 3. Merge to main
git checkout main
git merge release/1.x.x
git push origin main

# 4. Monitor deployment
railway deployments list --project <id> --environment production

# 5. Critical monitoring (30 minutes)
# Check every 5 minutes

# 6. Extended monitoring (48 hours)
# Regular checks at +1h, +2h, +4h, +8h, +24h, +48h
```

### Rollback

```bash
# 1. List deployments
railway deployments list --project <id> --environment production

# 2. Rollback to previous
railway deployment rollback <previous-deployment-id> \
  --project <id> --environment production

# 3. Verify
curl https://togetherly.app/health

# 4. Notify team
# Post in Slack/incident channel
```

---

## 📖 Step-by-Step Guide

### Day Before Deployment

1. ✅ Complete feature development
2. ✅ Run `./scripts/pre_deployment_check.sh staging`
3. ✅ Ensure all CI checks pass
4. ✅ Get code review approval
5. ✅ Deploy to staging
6. ✅ Validate staging (4+ hours)
7. ✅ Sign off staging

### Deployment Day (Tuesday-Thursday, 10 AM - 2 PM)

1. ✅ Pre-production checklist complete
2. ✅ Team briefing (10:15 AM)
3. ✅ Database backup (10:30 AM)
4. ✅ Create release branch (10:45 AM)
5. ✅ Deploy to production (11:00 AM)
6. ✅ Immediate validation (11:05 AM)
7. ✅ Critical monitoring (11:05 - 11:35 AM, every 5 min)
8. ✅ Extended checks (+1h, +2h, +4h, +8h, +24h, +48h)
9. ✅ Sign off after 48 hours
10. ✅ Post-mortem / lessons learned

---

## 🎓 Best Practices

### Do's ✅

- ✅ Deploy during business hours (10 AM - 2 PM)
- ✅ Deploy Tuesday-Thursday
- ✅ Keep staging identical to production
- ✅ Monitor closely for first 30 minutes
- ✅ Document all changes in CHANGELOG
- ✅ Run automated checks before deploying
- ✅ Have rollback plan ready
- ✅ Notify team of deployment window
- ✅ Test migrations on staging first
- ✅ Keep backups current

### Don'ts ❌

- ❌ Don't deploy on Friday
- ❌ Don't deploy late in the day
- ❌ Don't skip staging validation
- ❌ Don't deploy without tests passing
- ❌ Don't deploy without code review
- ❌ Don't ignore warning signs
- ❌ Don't hesitate to rollback
- ❌ Don't deploy breaking database changes without planning
- ❌ Don't deploy without monitoring configured
- ❌ Don't deploy right before holidays/weekends

---

## 🆘 Troubleshooting

### Common Issues

1. **Deployment fails**
   - Check Railway logs
   - Verify environment variables
   - Check database connection
   - Review build logs

2. **High error rate**
   - Check application logs
   - Verify external services (Stripe, Gemini)
   - Check database queries
   - Consider rollback

3. **Slow response times**
   - Check database query performance
   - Review resource usage (CPU, memory)
   - Check for N+1 queries
   - Scale resources if needed

4. **Database connection issues**
   - Verify DATABASE_URL is set
   - Check connection pool settings
   - Review long-running queries
   - Check database server health

---

## 📞 Support and Resources

### Documentation
- **This guide**: DEPLOYMENT_GUIDE_PR180_PLUS.md
- **Checklist**: DEPLOYMENT_CHECKLIST_PR180_PLUS.md
- **Flow diagram**: DEPLOYMENT_FLOW_DIAGRAM.md
- **Original runbook**: DEPLOYMENT.md

### External Resources
- **Railway Docs**: https://docs.railway.app/
- **Railway Status**: https://status.railway.app/
- **GitHub Actions**: https://github.com/humble-scott-jones/eazeily/actions

### Scripts
- **Pre-deployment validation**: `./scripts/pre_deployment_check.sh`
- **Test suite**: `./run_tests.sh`

---

## 🔐 Security Considerations

### Pre-Deployment
- [ ] No secrets in code
- [ ] Gitleaks scan passed
- [ ] Dependencies scanned for vulnerabilities
- [ ] .env file not tracked in git

### Post-Deployment
- [ ] HTTPS enforced
- [ ] Secure cookies enabled
- [ ] Rate limiting active
- [ ] Security headers configured
- [ ] No sensitive data in logs

---

## 📝 Changelog and Versioning

### Update Documentation
When making significant deployment process changes:

1. Update relevant documentation files
2. Update this README
3. Document in CHANGELOG.md
4. Notify team of process changes

### Version History
- **v1.0.0** (Current): Initial comprehensive deployment guide for PR180+
  - Added DEPLOYMENT_GUIDE_PR180_PLUS.md
  - Added DEPLOYMENT_CHECKLIST_PR180_PLUS.md
  - Added DEPLOYMENT_FLOW_DIAGRAM.md
  - Added pre_deployment_check.sh script

---

## 🤝 Contributing

### Improving This Documentation

If you find issues or have improvements:

1. Create a feature branch
2. Update the relevant documentation
3. Test any script changes
4. Submit a PR with description
5. Get review from team

### Feedback

We welcome feedback on these deployment docs:
- What's unclear?
- What's missing?
- What worked well?
- What could be improved?

---

## Summary

This deployment documentation provides a comprehensive, regression-free path for deploying PR180 and beyond. Follow the guides, use the checklist, run the scripts, and monitor closely. When in doubt, rollback and investigate.

**Remember**: A delayed deployment is better than a broken production environment.

**Good luck with your deployment! 🚀**
