---
name: 🚀 Must-Have 4 - Deployment Pipeline & Environment Separation
about: Staging and production environments with protected deploys
title: '[LAUNCH] Deployment Pipeline & Environment Separation'
labels: ['launch', 'infra', 'high-priority', 'devops']
assignees: []
---

## Priority
**Must-Have #4** - Complete before launch

## Description
Set up proper staging and production environments with separate configurations. Production deploys should require approvals and pass all checks.

## Acceptance Criteria
- [ ] Staging environment set up and accessible
- [ ] Production environment configured
- [ ] Separate databases for staging and production
- [ ] Separate secrets/credentials for each environment
- [ ] Deployment workflows exist for both environments
- [ ] Protected production deploys require approvals
- [ ] Branch protection requiring reviews/CI for main branch
- [ ] Rollback capability documented and tested

## Implementation Tasks
- [ ] Set up staging environment infrastructure
- [ ] Set up production environment infrastructure
- [ ] Create deployment workflow for staging
- [ ] Create deployment workflow for production
- [ ] Configure environment-specific variables
- [ ] Set up GitHub environments with protection rules
- [ ] Configure required reviewers for production deploys
- [ ] Test deployment to staging
- [ ] Document deployment procedures
- [ ] Create rollback runbook
- [ ] Set up deployment notifications (Slack/email)

## Environment Configuration
```yaml
Staging:
  - Branch: main (auto-deploy on merge)
  - Approvals: None
  - URL: staging.swelly.app (or similar)
  
Production:
  - Branch: main (manual trigger with approval)
  - Approvals: Required (2+ reviewers)
  - URL: swelly.app
```

## Current State
- ⚠️ Need to verify environment separation
- ⚠️ Need deployment workflows
- ⚠️ Need approval gates

## Dependencies
- Secrets management (#1)

## Resources
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [Cloud Run Deployment](https://cloud.google.com/run/docs/deploying) (if using GCP)

## Definition of Done
- All acceptance criteria met
- Successful test deployment to both environments
- Team trained on deployment process
- Deployment runbook created and reviewed
