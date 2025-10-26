# Security Checklist for Production Deployment

Use this checklist to ensure all security measures are in place before and after production deployment.

## Pre-Deployment Security Checklist

### Secrets Management
- [ ] All production secrets are stored in Google Cloud Secret Manager (not in code or config files)
- [ ] No secrets are committed to version control (check with `git log --all --full-history --source -- **/.env*`)
- [ ] `.env` files are in `.gitignore` and never committed
- [ ] Test/development credentials are separate from production credentials
- [ ] Secrets follow naming conventions (e.g., `flask-secret-key`, `stripe-secret-key-production`)
- [ ] All secrets have been rotated from their default/example values
- [ ] Secret Manager API is enabled in GCP project

### IAM and Access Control
- [ ] Service accounts created with descriptive names (e.g., `togetherly-prod`)
- [ ] Service accounts follow least-privilege principle (access to specific secrets only)
- [ ] No overly broad IAM roles granted (e.g., `roles/owner`, `roles/editor`)
- [ ] Separate service accounts for each environment (dev, staging, prod)
- [ ] Human users have appropriate roles based on their responsibilities
- [ ] Service account keys are rotated regularly (if using key-based auth)
- [ ] Workload Identity Federation is considered as alternative to keys
- [ ] IAM policy bindings are documented

### GitHub Actions & CI/CD
- [ ] GitHub secret scanning is enabled for the repository
- [ ] Pre-commit hooks are installed (`pre-commit install`)
- [ ] Gitleaks or similar tool is integrated in CI pipeline
- [ ] Environment protection rules are configured (production requires approval)
- [ ] GitHub Actions secrets are properly scoped to environments
- [ ] CI/CD workflows never echo or log secret values
- [ ] Service account for GitHub Actions has minimum required permissions
- [ ] Workflow files reviewed for security issues

### Application Security
- [ ] Health check endpoint (`/_health`) is implemented and tested
- [ ] Flask `SECRET_KEY` is generated with cryptographically secure random value
- [ ] Debug mode is disabled in production (`FLASK_ENV=production`)
- [ ] Database queries use parameterized statements (SQL injection protection)
- [ ] User inputs are validated and sanitized
- [ ] HTTPS is enforced for all production traffic
- [ ] Security headers are configured (CSP, X-Frame-Options, etc.)
- [ ] Rate limiting is implemented for API endpoints
- [ ] Session cookies have `Secure` and `HttpOnly` flags in production
- [ ] CORS is properly configured (not `*` for production)

### Stripe Integration
- [ ] Using production Stripe keys (`sk_live_*`, `pk_live_*`)
- [ ] Webhook signature verification is implemented
- [ ] Webhook secret is stored in Secret Manager
- [ ] Test credit cards are not hardcoded
- [ ] Payment error handling is robust
- [ ] PCI compliance requirements are understood and met
- [ ] Stripe API version is pinned and tested

### Infrastructure
- [ ] Container image is built from official Python base image
- [ ] Non-root user is configured in Dockerfile
- [ ] Only necessary files are included in container (`.dockerignore` configured)
- [ ] Container vulnerability scanning is enabled
- [ ] Cloud Run service account has minimum permissions
- [ ] Auto-scaling limits are configured appropriately
- [ ] Cloud Armor or similar DDoS protection is considered
- [ ] Cloud CDN is configured for static assets (if applicable)

### Monitoring and Logging
- [ ] Application logging is configured (but never logs secrets!)
- [ ] Cloud Logging is enabled
- [ ] Uptime checks are configured
- [ ] Alerting is set up for critical errors
- [ ] Audit logs are enabled for Secret Manager access
- [ ] Log retention policies are configured
- [ ] Monitoring dashboard is created
- [ ] On-call rotation is established

### Documentation
- [ ] Secrets rotation schedule is documented
- [ ] Emergency contact information is up to date
- [ ] Runbook procedures are documented and tested
- [ ] Team members are trained on security procedures
- [ ] Deployment process is documented
- [ ] Rollback procedures are documented and tested

## Post-Deployment Security Checklist

### Immediate (Within 24 hours)
- [ ] Health check endpoint is responding correctly
- [ ] Application logs show no errors or warnings
- [ ] All features are functional in production
- [ ] Stripe integration is working (test with small transaction)
- [ ] Secret Manager audit logs show expected access patterns
- [ ] No secrets are visible in Cloud Logging output
- [ ] HTTPS certificate is valid and properly configured
- [ ] DNS is pointing to correct Cloud Run service

### Within First Week
- [ ] Monitor application performance and resource usage
- [ ] Review all audit logs for unexpected access
- [ ] Test emergency runbook procedures
- [ ] Verify backup/restore procedures (if applicable)
- [ ] Review and address any security alerts from Google Security Command Center
- [ ] Conduct internal security review of deployment
- [ ] Update team documentation based on deployment learnings

### Ongoing (Monthly)
- [ ] Review IAM bindings for appropriateness
- [ ] Audit Secret Manager access logs
- [ ] Review application logs for security issues
- [ ] Check for dependency updates and security patches
- [ ] Verify monitoring and alerting are working
- [ ] Review and update rotation schedule
- [ ] Conduct security awareness training for team

### Quarterly
- [ ] Rotate production secrets per schedule
- [ ] Review and update security documentation
- [ ] Conduct penetration testing (if required)
- [ ] Review third-party integrations (Stripe, OpenAI, etc.)
- [ ] Update team on new security features and best practices
- [ ] Review incident response procedures
- [ ] Audit all service account keys and rotate if needed

## Compliance and Legal

- [ ] Privacy policy is up to date and accessible
- [ ] Terms of service are clearly stated
- [ ] GDPR compliance (if serving EU users)
- [ ] CCPA compliance (if serving California users)
- [ ] Data retention policies are implemented
- [ ] User data deletion process is documented
- [ ] Cookie consent is implemented (if required)
- [ ] Payment processor agreement is signed (Stripe)

## Incident Response Preparedness

- [ ] Security incident response plan is documented
- [ ] Team knows who to contact in case of security incident
- [ ] Emergency revocation procedures are tested
- [ ] Backup communication channels are established
- [ ] Post-incident review template is ready
- [ ] Legal counsel contact information is documented
- [ ] PR/communications plan for security incidents is prepared

## Tools and Automation

- [ ] Pre-commit hooks are configured: `pre-commit install`
- [ ] Secrets scanning is automated in CI/CD
- [ ] Dependency vulnerability scanning is enabled (Dependabot, Snyk, etc.)
- [ ] Container vulnerability scanning is enabled
- [ ] Static application security testing (SAST) is considered
- [ ] Dynamic application security testing (DAST) is considered for production
- [ ] Infrastructure as Code (IaC) security scanning (if using Terraform, etc.)

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Security Lead | [Name] | [Email/Phone] |
| DevOps Lead | [Name] | [Email/Phone] |
| CTO/Technical Lead | [Name] | [Email/Phone] |
| On-Call Engineer | [Rotation] | [PagerDuty/Slack] |
| Google Cloud Support | N/A | [Support Case URL] |
| Stripe Support | N/A | https://support.stripe.com |

## Useful Commands for Security Auditing

```bash
# List all secrets
gcloud secrets list --project=PROJECT_ID

# View IAM policy for a secret
gcloud secrets get-iam-policy SECRET_NAME --project=PROJECT_ID

# View recent secret access
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" \
  --project=PROJECT_ID --limit=50

# List service accounts
gcloud iam service-accounts list --project=PROJECT_ID

# View service account IAM bindings
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*"

# Check for exposed secrets in git history
git log --all --full-history --source -- **/.env*

# Scan for secrets with Gitleaks
gitleaks detect --source . --verbose

# List Cloud Run services
gcloud run services list --platform=managed

# View Cloud Run service configuration
gcloud run services describe SERVICE_NAME \
  --platform=managed --region=REGION
```

## Sign-Off

Before deploying to production, the following individuals must sign off:

- [ ] Developer: _________________ Date: _______
- [ ] Security Review: _________________ Date: _______
- [ ] DevOps/SRE: _________________ Date: _______
- [ ] Technical Lead: _________________ Date: _______

## Notes

Additional security considerations for this deployment:

_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
