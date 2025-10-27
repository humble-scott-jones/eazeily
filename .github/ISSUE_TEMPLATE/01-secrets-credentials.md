---
name: 🔐 Must-Have 1 - Secrets & Credentials
about: Use a secrets manager for all production secrets
title: '[LAUNCH] Secrets & Credentials Management'
labels: ['launch', 'infra', 'high-priority', 'security']
assignees: []
---

## Priority
**Must-Have #1** - Complete before launch

## Description
Use a secrets manager (Google Secret Manager if on GCP) for all production secrets. No production secrets should be stored in the repository or directly in the database.

## Acceptance Criteria
- [ ] No production secret stored in repo or Firestore/database
- [ ] Service accounts/roles configured with appropriate permissions
- [ ] Documented rotation steps for all secrets
- [ ] Secrets manager integration tested in staging environment
- [ ] All environment variables migrated to secrets manager
- [ ] Access audit log enabled for secrets manager

## Implementation Tasks
- [ ] Set up Google Secret Manager (or equivalent)
- [ ] Create service account with minimal required permissions
- [ ] Migrate all production secrets from .env to secrets manager
- [ ] Update deployment scripts to fetch secrets from manager
- [ ] Document secret rotation procedures
- [ ] Test secret rotation in staging
- [ ] Create runbook for emergency secret rotation

## Dependencies
- None (highest priority)

## Resources
- [Google Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [Azure Key Vault](https://azure.microsoft.com/en-us/services/key-vault/)

## Definition of Done
- All acceptance criteria met
- Tested in staging environment
- Documentation updated
- Team trained on secret management procedures
