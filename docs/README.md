# Security Documentation

This directory contains comprehensive security documentation for the Togetherly application.

## 📚 Documentation Overview

### Core Security Documents

1. **[SECRETS_MANAGEMENT.md](./SECRETS_MANAGEMENT.md)** - *Start Here*
   - Complete guide to secure secrets management
   - Google Cloud Secret Manager setup
   - Local development configuration
   - CI/CD integration
   - Audit logging procedures

2. **[SECRETS_ROTATION_RUNBOOK.md](./SECRETS_ROTATION_RUNBOOK.md)** - *Operational Procedures*
   - Step-by-step rotation procedures for all secret types
   - Emergency revocation procedures
   - Incident response templates
   - Useful commands reference
   - Contact information

3. **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** - *Production Deployment*
   - Cloud Run deployment instructions
   - IAM and access control setup
   - Service account configuration
   - Environment protection
   - Health checks and monitoring

4. **[SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)** - *Pre/Post-Deployment Verification*
   - Comprehensive security checklist
   - Pre-deployment requirements
   - Post-deployment verification
   - Ongoing maintenance tasks
   - Compliance considerations

## 🚀 Quick Start

### For Developers (Local Development)

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Fill in your **test** credentials (never use production secrets locally):
   ```bash
   # Edit .env with test keys from Stripe dashboard
   STRIPE_SECRET_KEY=sk_test_...
   ```

3. Install pre-commit hooks to prevent accidental secret commits:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

4. Read [SECRETS_MANAGEMENT.md](./SECRETS_MANAGEMENT.md) for complete setup guide.

### For DevOps (Production Deployment)

1. Read [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for complete deployment process
2. Set up Google Cloud Secret Manager with production secrets
3. Configure IAM roles and service accounts
4. Deploy using provided GitHub Actions workflow
5. Verify deployment using [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)

### For Security Team

1. Review [SECRETS_MANAGEMENT.md](./SECRETS_MANAGEMENT.md) for architecture
2. Audit IAM permissions and secret access patterns
3. Set up monitoring and alerting per [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
4. Schedule regular secret rotation using [SECRETS_ROTATION_RUNBOOK.md](./SECRETS_ROTATION_RUNBOOK.md)
5. Conduct periodic security reviews using [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)

## 🔐 Security Principles

This documentation is built on the following security principles:

1. **Never commit secrets to version control** - Use Secret Manager for production, `.env` for local dev only
2. **Least privilege access** - Grant only necessary permissions to each service and user
3. **Defense in depth** - Multiple layers of security (pre-commit hooks, CI scanning, IAM, audit logs)
4. **Assume compromise** - Have procedures ready for when (not if) secrets are compromised
5. **Audit everything** - Log all secret access with timestamps and user information
6. **Regular rotation** - Rotate secrets on a schedule, not just when compromised
7. **Separation of environments** - Use completely different secrets for dev/staging/prod

## 📋 Common Tasks

### Rotating a Secret

See [SECRETS_ROTATION_RUNBOOK.md](./SECRETS_ROTATION_RUNBOOK.md) for detailed procedures.

Quick reference:
```bash
# 1. Create new secret version
echo -n "NEW_SECRET_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

# 2. Deploy application with new secret
gcloud run deploy togetherly --update-secrets=ENV_VAR=SECRET_NAME:latest

# 3. Verify deployment
curl https://your-app.run.app/_health

# 4. Disable old secret version (after verification)
gcloud secrets versions disable OLD_VERSION --secret=SECRET_NAME
```

### Emergency Secret Revocation

If a secret is compromised:

1. **Immediately** disable the secret in its source (e.g., Stripe dashboard)
2. Follow [SECRETS_ROTATION_RUNBOOK.md - Emergency Revocation](./SECRETS_ROTATION_RUNBOOK.md#emergency-revocation-procedures)
3. Generate and deploy new secret
4. Review audit logs for unauthorized access
5. Document incident using provided template

### Auditing Secret Access

```bash
# View recent secret access (last 7 days)
./scripts/audit-secrets.sh 7

# Or manually with gcloud
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" \
  --project=PROJECT_ID --limit=50
```

### Pre-commit Hook Setup

Prevent accidental secret commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks defined in .pre-commit-config.yaml
pre-commit install

# Run manually on all files
pre-commit run --all-files
```

## 🛠️ Tools and Utilities

### Python Utilities

- **`secrets_util.py`** - Secret Manager integration module
  - Automatic fallback to environment variables in dev
  - Caching to reduce API calls
  - Audit logging of secret access

### Shell Scripts

- **`scripts/fetch-secrets.sh`** - Fetch secrets from Secret Manager for local debugging
- **`scripts/audit-secrets.sh`** - Audit secret access logs

### CI/CD Integration

- **`.pre-commit-config.yaml`** - Pre-commit hooks for secret detection
- **`.github/workflows/ci.yml`** - Enhanced with Gitleaks scanning
- **`.github/workflows/deploy-production.yml.example`** - Production deployment template

## 🆘 Emergency Contacts

See [SECRETS_ROTATION_RUNBOOK.md - Contact Information](./SECRETS_ROTATION_RUNBOOK.md#contact-information) for:
- On-call rotation
- Escalation path
- External support contacts

## 📖 Additional Resources

### External Documentation

- [Google Cloud Secret Manager Docs](https://cloud.google.com/secret-manager/docs)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Stripe Security Best Practices](https://stripe.com/docs/security)

### Repository Files

- `/.pre-commit-config.yaml` - Pre-commit hook configuration
- `/.env.example` - Example environment variables with security notes
- `/Dockerfile` - Production container configuration
- `/secrets_util.py` - Secret management utility module
- `/scripts/` - Utility scripts for secret management

## 🔄 Document Maintenance

These documents should be reviewed and updated:

- **Monthly**: Verify contact information and on-call rotation
- **Quarterly**: Review procedures against actual practices
- **After incidents**: Update based on lessons learned
- **When changing tools**: Update integration guides

Last updated: 2025-10-26

---

💡 **Tip**: Bookmark this README and share it with new team members as their starting point for security documentation.

⚠️ **Important**: If you find any security issues or have suggestions for improving these documents, please report them to the security team immediately.
