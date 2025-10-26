---
name: 🔐 Must-Have 10 - Access Controls & Least Privilege
about: IAM configured for services and humans, admin roles restricted
title: '[LAUNCH] Access Controls & Least Privilege'
labels: ['launch', 'security', 'high-priority', 'infra']
assignees: []
---

## Priority
**Must-Have #10** - Complete before launch

## Description
Configure IAM (Identity and Access Management) for all services and team members following the principle of least privilege. Ensure admin roles are restricted and no wide-permission tokens are in use.

## Acceptance Criteria
- [ ] Access matrix documented for all team members
- [ ] Service accounts configured with minimal permissions
- [ ] Admin roles restricted to specific individuals
- [ ] No wide-permission tokens in use
- [ ] Regular access reviews scheduled
- [ ] MFA enabled for all admin accounts
- [ ] Audit logging enabled for access changes
- [ ] Emergency access procedures documented

## Implementation Tasks
- [ ] Document current access requirements
- [ ] Create access matrix (who needs what)
- [ ] Configure service accounts with minimal permissions
- [ ] Set up role-based access control (RBAC)
- [ ] Enable MFA for all admin accounts
- [ ] Review and revoke unnecessary permissions
- [ ] Set up audit logging
- [ ] Create access request/approval workflow
- [ ] Schedule quarterly access reviews
- [ ] Document emergency access procedures
- [ ] Test access controls in staging

## Access Matrix Template

| Role | Production DB | Secrets Manager | Deployment | Monitoring | Admin Panel |
|------|---------------|-----------------|------------|------------|-------------|
| Developer | Read | No | Staging Only | Read | No |
| DevOps | Read/Write | Read/Write | All | Read/Write | Yes |
| Admin | Read | Read | Production | Read/Write | Yes |
| Service Account | Read/Write | Read | No | Write | No |

## Service Account Permissions

```yaml
content-generator-service:
  permissions:
    - database.read
    - database.write
    - logging.write
  no_permissions:
    - secrets.manage
    - deployment.manage
    - user.manage

deployment-service:
  permissions:
    - deployment.create
    - deployment.read
    - secrets.read
  no_permissions:
    - database.admin
    - user.delete
```

## Security Controls
- [ ] Enforce MFA for admin access
- [ ] Rotate service account keys regularly
- [ ] Monitor for privilege escalation attempts
- [ ] Alert on admin role assignments
- [ ] Regular permission audits
- [ ] Temporary elevated access with auto-expiry

## Admin Access
```
Current Admins (from ADMIN_EMAILS):
- Verify list and ensure it's current
- Ensure each has MFA enabled
- Document responsibilities
```

## Current State
- ⚠️ Review current admin access
- ⚠️ Need access matrix documentation
- ⚠️ Need service account audit

## Dependencies
- Secrets management (#1)
- Production environment (#4)

## Resources
- [Google Cloud IAM Best Practices](https://cloud.google.com/iam/docs/best-practices)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Principle of Least Privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege)

## Definition of Done
- All acceptance criteria met
- Access matrix reviewed and approved
- All admin accounts have MFA
- Audit logging verified
- Team trained on access policies
