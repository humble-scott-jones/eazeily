# Secrets Management Guide

## Overview

This document describes how to securely manage production secrets (API keys, database passwords, OAuth client secrets) for the Togetherly application.

## ⚠️ Security Principles

1. **Never commit secrets to version control** - Use `.env` files locally (already gitignored) and secret managers for production
2. **Least privilege access** - Grant secrets access only to services that need them
3. **Rotation and revocation** - Regularly rotate secrets and have procedures to revoke compromised secrets
4. **Audit logging** - Track who accesses secrets and when
5. **Environment separation** - Use different secrets for development, staging, and production

## Production Secret Storage (Recommended: Google Cloud Secret Manager)

### Why Google Cloud Secret Manager?

For Firebase/GCP-hosted workloads, Google Cloud Secret Manager is the recommended solution because:
- Native integration with Firebase Functions and Cloud Run
- IAM-based access control
- Automatic audit logging via Cloud Audit Logs
- Encryption at rest and in transit
- Versioning and rotation support
- Free tier: 10,000 access operations per month

### Setting Up Google Cloud Secret Manager

#### 1. Enable the Secret Manager API

```bash
gcloud services enable secretmanager.googleapis.com
```

#### 2. Create Secrets

```bash
# Example: Create a secret for Stripe API key
echo -n "sk_live_YOUR_SECRET_KEY" | gcloud secrets create stripe-secret-key \
  --data-file=- \
  --replication-policy="automatic"

# Create other secrets
echo -n "your-secret-value" | gcloud secrets create openai-api-key --data-file=-
echo -n "your-flask-secret" | gcloud secrets create flask-secret-key --data-file=-
echo -n "your-webhook-secret" | gcloud secrets create stripe-webhook-secret --data-file=-
```

#### 3. Grant Access to Service Accounts

```bash
# Grant access to your Cloud Run/Functions service account
gcloud secrets add-iam-policy-binding stripe-secret-key \
  --member="serviceAccount:YOUR-PROJECT@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### 4. Access Secrets in Application Code

Add to your `requirements.txt`:
```
google-cloud-secret-manager>=2.16.0
```

Example code to fetch secrets:

```python
from google.cloud import secretmanager
import os

def get_secret(secret_id, project_id=None, version="latest"):
    """
    Fetch a secret from Google Cloud Secret Manager.
    
    Args:
        secret_id: The ID of the secret
        project_id: GCP project ID (defaults to environment)
        version: Secret version (default: "latest")
    
    Returns:
        The secret value as a string
    """
    if project_id is None:
        project_id = os.getenv('GCP_PROJECT_ID')
        
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
    
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        # Log error but don't expose secret details
        print(f"Failed to fetch secret {secret_id}: {type(e).__name__}")
        raise

# Usage in app.py
if os.getenv('FLASK_ENV') == 'production':
    STRIPE_SECRET_KEY = get_secret('stripe-secret-key')
    FLASK_SECRET_KEY = get_secret('flask-secret-key')
else:
    # Use .env file for local development
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    FLASK_SECRET_KEY = os.getenv('SECRET_KEY')
```

### Alternative: GitHub Actions Secrets + Environment Protection

For build-time secrets or CI/CD:

1. Go to Settings > Secrets and variables > Actions
2. Create environment-specific secrets (production, staging)
3. Set up environment protection rules requiring reviews for production deployments
4. Reference secrets in workflows:

```yaml
jobs:
  deploy:
    environment: production  # Requires approval
    env:
      STRIPE_SECRET_KEY: ${{ secrets.STRIPE_SECRET_KEY }}
```

## Local Development

### Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Fill in your **test/development** credentials:
```bash
# .env
SECRET_KEY=local-dev-secret-change-me
FLASK_ENV=development
STRIPE_SECRET_KEY=sk_test_YOUR_TEST_KEY
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_TEST_KEY
# ... other test credentials
```

3. **Never commit your `.env` file** - It's already in `.gitignore`

### Fetching Production Secrets Locally (Admin Only)

For authorized developers who need to debug production issues:

```bash
# Set up gcloud authentication
gcloud auth login
gcloud config set project YOUR-PROJECT-ID

# Fetch a specific secret
gcloud secrets versions access latest --secret="stripe-secret-key"

# Fetch all secrets and populate .env (use with caution!)
./scripts/fetch-secrets.sh production > .env.production
```

⚠️ **Warning**: Only authorized personnel should access production secrets. Never commit populated .env files.

## CI/CD Integration

### GitHub Actions

Secrets are configured in GitHub and injected at runtime:

```yaml
env:
  SECRET_KEY: ${{ secrets.SECRET_KEY }}
  STRIPE_SECRET_KEY: ${{ secrets.STRIPE_SECRET_KEY }}
  # Never echo secrets in logs
```

**Important**: Never log or echo secrets in CI output. GitHub automatically masks registered secrets, but be cautious with derived values.

### Deployment to Cloud Run / Firebase Functions

Use Secret Manager integration:

```yaml
# cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
spec:
  template:
    spec:
      containers:
      - image: gcr.io/PROJECT/app
        env:
        - name: STRIPE_SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: stripe-secret-key
              key: latest
```

For Firebase Functions:

```javascript
// functions/index.js
const {SecretManagerServiceClient} = require('@google-cloud/secret-manager');
const client = new SecretManagerServiceClient();

async function getSecret(secretName) {
  const [version] = await client.accessSecretVersion({
    name: `projects/${process.env.GCP_PROJECT}/secrets/${secretName}/versions/latest`,
  });
  return version.payload.data.toString();
}
```

## Secret Rotation

See [SECRETS_ROTATION_RUNBOOK.md](./SECRETS_ROTATION_RUNBOOK.md) for detailed procedures.

## Preventing Secrets in Commits

1. **Pre-commit hooks** - See `.pre-commit-config.yaml`
2. **GitHub Secret Scanning** - Enabled by default for public repos
3. **Manual review** - Always review diffs before committing

## Audit Logging

### Google Cloud Secret Manager

View audit logs:

```bash
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" \
  --limit 50 \
  --format json
```

### Application-Level Logging

Log secret access attempts (but never log the secret values):

```python
import logging

logger = logging.getLogger(__name__)

def get_secret(secret_id):
    logger.info(f"Accessing secret: {secret_id}", extra={
        "secret_id": secret_id,
        "user": get_current_user(),
        "timestamp": datetime.utcnow().isoformat()
    })
    # ... fetch secret
```

## Environment-Specific Configuration

| Environment | Secret Source | Access Control |
|------------|---------------|----------------|
| **Local Dev** | `.env` file | Developer's machine only |
| **CI/CD** | GitHub Actions Secrets | Repository admins |
| **Staging** | Secret Manager (staging project) | Staging service account |
| **Production** | Secret Manager (prod project) | Production service account + manual approval |

## Security Checklist

- [ ] All production secrets are stored in Google Cloud Secret Manager (or equivalent)
- [ ] `.env` file is in `.gitignore` and never committed
- [ ] Service accounts follow least-privilege principle
- [ ] Pre-commit hooks are installed to catch accidental secret commits
- [ ] GitHub secret scanning is enabled
- [ ] Production deployments require manual approval
- [ ] Secrets are rotated regularly (see rotation schedule)
- [ ] Audit logging is enabled and monitored
- [ ] Emergency revocation procedures are documented

## Resources

- [Google Cloud Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Secrets Rotation Runbook](./SECRETS_ROTATION_RUNBOOK.md)

## Emergency Contacts

If you suspect a secret has been compromised:

1. **Immediately** revoke/rotate the secret (see runbook)
2. Notify the security team
3. Review audit logs for unauthorized access
4. Update all dependent services with new secrets
