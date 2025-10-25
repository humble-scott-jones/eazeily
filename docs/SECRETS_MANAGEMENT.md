# Secrets Management Guide

## Overview
This guide provides secure practices for managing secrets in production for the Togetherly application.

## Environment Variables Required

### Application Secrets
- `SECRET_KEY` - Flask session secret (required in production)
  - Generate: `python -c "import secrets; print(secrets.token_hex(32))"`
  - Store securely, never commit to version control

### Stripe Integration
- `STRIPE_PUBLISHABLE_KEY` - Public key for client-side Stripe.js
- `STRIPE_SECRET_KEY` - Secret key for server-side API calls
- `STRIPE_TEST_PRICE_ID` - Price ID for subscription plans
- `STRIPE_WEBHOOK_SECRET` - Webhook signature verification secret
- `STRIPE_SUCCESS_URL` - Redirect URL after successful payment
- `STRIPE_CANCEL_URL` - Redirect URL after canceled payment
- `STRIPE_MANAGE_URL` - Return URL for billing portal

### Admin & Access Control
- `ADMIN_EMAILS` - Comma-separated list of admin email addresses

### Optional Integrations
- `OPENAI_API_KEY` - OpenAI API key for AI content generation features

## Recommended Solutions for Production Secrets

### Option 1: Firebase Hosting + Cloud Functions (Recommended)

Firebase offers secure secrets management through environment configuration:

#### Setup Steps:
1. Install Firebase CLI: `npm install -g firebase-tools`
2. Initialize Firebase in your project: `firebase init`
3. Configure secrets using Firebase Functions:

```bash
# Set individual secrets
firebase functions:secrets:set SECRET_KEY
firebase functions:secrets:set STRIPE_SECRET_KEY
firebase functions:secrets:set STRIPE_WEBHOOK_SECRET

# View configured secrets (values hidden)
firebase functions:secrets:access
```

4. In your Cloud Function, secrets are automatically available:
```python
import os
secret_key = os.environ.get('SECRET_KEY')
```

#### Advantages:
- Native integration with Firebase services
- Automatic rotation support
- Access control via IAM
- Audit logging
- No additional cost for basic usage

### Option 2: Google Cloud Secret Manager

If using Google Cloud Platform infrastructure:

#### Setup Steps:
1. Enable Secret Manager API in GCP Console
2. Create secrets:
```bash
echo -n "your-secret-value" | gcloud secrets create SECRET_KEY --data-file=-
```

3. Grant access to your service account
4. Access in application:
```python
from google.cloud import secretmanager

def access_secret(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

#### Advantages:
- Centralized secret management
- Automatic encryption at rest
- Version history
- Fine-grained IAM permissions
- Integration with Cloud Audit Logs

### Option 3: AWS Secrets Manager

If deploying to AWS:

#### Setup Steps:
1. Create secrets in AWS Secrets Manager console or CLI:
```bash
aws secretsmanager create-secret \
    --name togetherly/SECRET_KEY \
    --secret-string "your-secret-value"
```

2. Access in application:
```python
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])
```

#### Advantages:
- Native AWS integration
- Automatic rotation
- Cross-service availability
- Encryption with AWS KMS
- Pay per secret/API call

### Option 4: HashiCorp Vault

For enterprise-grade secret management:

#### Setup Steps:
1. Deploy Vault server (self-hosted or HCP Vault)
2. Initialize and unseal Vault
3. Create secret engine and policies
4. Store secrets:
```bash
vault kv put secret/togetherly \
    SECRET_KEY="your-secret-value" \
    STRIPE_SECRET_KEY="sk_live_..."
```

5. Access in application using Vault client library

#### Advantages:
- Platform-agnostic
- Dynamic secrets generation
- Advanced access policies
- Comprehensive audit trail
- Multi-cloud support

### Option 5: Environment Variables via Hosting Platform

Most PaaS platforms (Heroku, Render, Railway, etc.) provide secure environment variable management:

#### Heroku Example:
```bash
heroku config:set SECRET_KEY="your-secret-value"
heroku config:set STRIPE_SECRET_KEY="sk_live_..."
```

#### Render Example:
Configure in dashboard under Environment tab or via render.yaml:
```yaml
services:
  - type: web
    name: togetherly
    env: python
    envVars:
      - key: SECRET_KEY
        sync: false  # Manual entry, not from repo
      - key: STRIPE_SECRET_KEY
        sync: false
```

#### Advantages:
- Simple setup
- Platform-integrated
- Automatic deployment integration
- No additional services needed

## Security Best Practices

### DO:
✅ Use different secrets for development, staging, and production
✅ Rotate secrets regularly (every 90 days recommended)
✅ Use strong, randomly generated secrets (minimum 32 characters)
✅ Implement secret access auditing
✅ Use least-privilege access policies
✅ Enable secret version history
✅ Use webhook signature verification (STRIPE_WEBHOOK_SECRET)
✅ Keep production secrets separate from development
✅ Document who has access to production secrets
✅ Use HTTPS/TLS for all API communications

### DON'T:
❌ Never commit secrets to version control (.env files should be in .gitignore)
❌ Never log secret values
❌ Never share secrets via email or chat
❌ Never use the same secret across multiple environments
❌ Never hardcode secrets in application code
❌ Never expose secrets in client-side code
❌ Never use weak or predictable secrets

## Secret Rotation Procedures

### Routine Rotation (Zero-Downtime):
1. Generate new secret value
2. Add new secret alongside old (if supported by service)
3. Update application to accept both old and new
4. Deploy application update
5. Remove old secret after verification
6. Update secret in management system

### Emergency Rotation (Suspected Compromise):
1. Immediately generate and deploy new secret
2. Revoke old secret
3. Investigate potential unauthorized access
4. Update all affected systems
5. Review audit logs
6. Document incident

## Webhook Secret Verification

Always verify Stripe webhook signatures in production:

```python
import stripe

def verify_webhook(payload, sig_header):
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
        return event
    except ValueError:
        # Invalid payload
        return None
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return None
```

## Monitoring & Alerts

Set up monitoring for:
- Failed authentication attempts with secrets
- Secret access patterns (unusual times or locations)
- API rate limiting events
- Stripe webhook signature failures
- Secret rotation deadlines

## Compliance Considerations

Depending on your requirements:
- **PCI DSS**: Required for handling payment card data
- **SOC 2**: Secret management audit requirements
- **GDPR**: Data protection for EU users
- **HIPAA**: If handling health information

## Emergency Contacts

Maintain a secure list of:
- Secret management system administrators
- On-call security contacts
- Stripe account administrators
- Cloud platform support contacts

## Additional Resources

- [Stripe Security Best Practices](https://stripe.com/docs/security)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Firebase Security Rules](https://firebase.google.com/docs/rules)
- [Cloud Security Alliance Guidelines](https://cloudsecurityalliance.org/)

## Regular Audit Checklist

Monthly:
- [ ] Review who has access to production secrets
- [ ] Check for any secrets in version control
- [ ] Review secret access logs
- [ ] Verify webhook signature validation is working

Quarterly:
- [ ] Rotate all production secrets
- [ ] Review and update access policies
- [ ] Test secret recovery procedures
- [ ] Update security documentation

Annually:
- [ ] Complete security audit
- [ ] Review secret management solution
- [ ] Update disaster recovery plans
- [ ] Train team on security best practices
