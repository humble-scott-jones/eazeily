# Production Deployment Guide with Secret Manager

This guide covers deploying Togetherly to production with secure secrets management using Google Cloud Secret Manager.

## Prerequisites

- Google Cloud Project set up
- `gcloud` CLI installed and authenticated
- Domain/DNS configured (if applicable)
- GitHub repository with Actions enabled

## Deployment Options

### Option 1: Cloud Run (Recommended)

Cloud Run provides serverless container deployment with automatic scaling and Secret Manager integration.

#### Step 1: Enable Required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

#### Step 2: Set Up Secrets

```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Create secrets (replace with actual production values)
echo -n "$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" | \
  gcloud secrets create flask-secret-key --data-file=-

echo -n "sk_live_YOUR_STRIPE_SECRET_KEY" | \
  gcloud secrets create stripe-secret-key --data-file=-

echo -n "pk_live_YOUR_STRIPE_PUBLISHABLE_KEY" | \
  gcloud secrets create stripe-publishable-key --data-file=-

echo -n "whsec_YOUR_WEBHOOK_SECRET" | \
  gcloud secrets create stripe-webhook-secret --data-file=-

echo -n "price_YOUR_PRICE_ID" | \
  gcloud secrets create stripe-price-id --data-file=-

# Optional: OpenAI key
echo -n "sk-YOUR_OPENAI_KEY" | \
  gcloud secrets create openai-api-key --data-file=-

# Admin emails
echo -n "admin@example.com,admin2@example.com" | \
  gcloud secrets create admin-emails --data-file=-
```

#### Step 3: Build and Deploy

```bash
# Build the container
gcloud builds submit --tag gcr.io/$PROJECT_ID/togetherly

# Deploy to Cloud Run with secrets
gcloud run deploy togetherly \
  --image gcr.io/$PROJECT_ID/togetherly \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars FLASK_ENV=production \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --set-secrets=SECRET_KEY=flask-secret-key:latest \
  --set-secrets=STRIPE_SECRET_KEY=stripe-secret-key:latest \
  --set-secrets=STRIPE_PUBLISHABLE_KEY=stripe-publishable-key:latest \
  --set-secrets=STRIPE_WEBHOOK_SECRET=stripe-webhook-secret:latest \
  --set-secrets=STRIPE_TEST_PRICE_ID=stripe-price-id:latest \
  --set-secrets=OPENAI_API_KEY=openai-api-key:latest \
  --set-secrets=ADMIN_EMAILS=admin-emails:latest \
  --memory 512Mi \
  --cpu 1 \
  --max-instances 10 \
  --min-instances 0
```

#### Step 4: Configure Custom Domain (Optional)

```bash
gcloud run domain-mappings create \
  --service togetherly \
  --domain your-domain.com \
  --region us-central1
```

### Option 2: Firebase Functions

If you're using Firebase for hosting and need serverless functions:

#### Setup

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize Firebase
firebase init functions

# Install dependencies in functions directory
cd functions
npm install @google-cloud/secret-manager
```

#### Configure Secret Access

```javascript
// functions/index.js
const {SecretManagerServiceClient} = require('@google-cloud/secret-manager');
const functions = require('firebase-functions');

const secretClient = new SecretManagerServiceClient();

async function getSecret(secretName) {
  const projectId = process.env.GCP_PROJECT || process.env.GCLOUD_PROJECT;
  const [version] = await secretClient.accessSecretVersion({
    name: `projects/${projectId}/secrets/${secretName}/versions/latest`,
  });
  return version.payload.data.toString('utf8');
}

exports.app = functions.https.onRequest(async (req, res) => {
  // Fetch secrets at function initialization
  const stripeKey = await getSecret('stripe-secret-key');
  // ... use in your app
});
```

#### Deploy

```bash
firebase deploy --only functions
```

### Option 3: App Engine

```bash
# Create app.yaml
cat > app.yaml << EOF
runtime: python39
env: standard

env_variables:
  FLASK_ENV: production
  GCP_PROJECT_ID: $PROJECT_ID

# No secrets in app.yaml - use Secret Manager
EOF

# Deploy
gcloud app deploy
```

## IAM and Access Control

### Service Account Setup

#### Create Service Account for Production

```bash
# Create service account
gcloud iam service-accounts create togetherly-prod \
  --display-name "Togetherly Production" \
  --description "Service account for Togetherly production workload"

# Get service account email
SA_EMAIL="togetherly-prod@$PROJECT_ID.iam.gserviceaccount.com"

# Grant Secret Manager access (least privilege)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

#### Grant Access to Specific Secrets Only (More Secure)

```bash
# Grant access to individual secrets instead of project-wide access
for secret in flask-secret-key stripe-secret-key stripe-publishable-key stripe-webhook-secret; do
  gcloud secrets add-iam-policy-binding $secret \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/secretmanager.secretAccessor"
done
```

### Human User Access

#### For Administrators

```bash
# Grant admin full access to secrets
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:admin@example.com" \
  --role="roles/secretmanager.admin"
```

#### For Developers (Read-Only)

```bash
# Grant developers read-only access for debugging
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:developer@example.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### For CI/CD (GitHub Actions)

```bash
# Create service account for GitHub Actions
gcloud iam service-accounts create github-actions \
  --display-name "GitHub Actions CI/CD"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Grant secret access
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Create and download key for GitHub Actions
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com

# Add to GitHub Secrets
# Go to: Settings > Secrets and variables > Actions
# Create new secret: GCP_SA_KEY with contents of github-actions-key.json
```

### IAM Best Practices

1. **Least Privilege**: Grant minimum permissions needed
2. **Service Account per Environment**: Use separate accounts for dev/staging/prod
3. **Regular Audits**: Review IAM bindings quarterly
4. **Time-Bound Access**: Use temporary tokens when possible
5. **Separate Humans from Services**: Don't use personal accounts for services

### Audit Logging

Enable audit logging for secret access:

```bash
# Audit logs are enabled by default for Secret Manager
# View audit logs
gcloud logging read "resource.type=secretmanager.googleapis.com/Secret" \
  --limit 50 \
  --format json
```

Set up monitoring alerts:

```bash
# Create alert policy for unusual secret access
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="Unusual Secret Access Pattern" \
  --condition-display-name="High frequency secret access" \
  --condition-threshold-value=100 \
  --condition-threshold-duration=60s \
  --condition-filter='resource.type="secretmanager.googleapis.com/Secret"
    AND metric.type="secretmanager.googleapis.com/secret/access_count"'
```

## Environment Protection in GitHub Actions

### Set Up Protected Environments

1. Go to: Settings > Environments
2. Create environments: `production`, `staging`
3. For production:
   - ✅ Required reviewers: Add team members
   - ✅ Wait timer: 5 minutes (optional)
   - ✅ Deployment branches: Only `main`

### Use in Workflow

```yaml
# .github/workflows/deploy-production.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Requires approval before running
    steps:
      - uses: actions/checkout@v4
      
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy togetherly \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/togetherly:${{ github.sha }} \
            --region us-central1 \
            --platform managed
```

## Health Checks and Monitoring

### Add Health Check Endpoint

```python
# app.py
@app.get('/_health')
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': os.getenv('APP_VERSION', 'unknown')
    })
```

### Set Up Uptime Checks

```bash
# Create uptime check
gcloud monitoring uptime create https \
  --display-name="Togetherly Production Health" \
  --resource-type=uptime-url \
  --resource-url=https://your-domain.com/_health \
  --period=60
```

## Rollback Procedure

### Cloud Run Rollback

```bash
# List recent revisions
gcloud run revisions list --service togetherly --region us-central1

# Rollback to previous revision
gcloud run services update-traffic togetherly \
  --to-revisions REVISION_NAME=100 \
  --region us-central1
```

### Emergency Secret Rotation

If secrets are compromised, follow the emergency procedures in [SECRETS_ROTATION_RUNBOOK.md](./SECRETS_ROTATION_RUNBOOK.md).

## Checklist: Production Deployment

- [ ] All secrets stored in Secret Manager (not environment variables or code)
- [ ] Service account created with least-privilege IAM roles
- [ ] Secrets granted to service account (not project-wide access)
- [ ] Audit logging enabled and monitored
- [ ] Health check endpoint configured
- [ ] Uptime monitoring set up
- [ ] GitHub environment protection enabled for production
- [ ] Rollback procedure tested
- [ ] Emergency contacts documented
- [ ] Secrets rotation schedule established
- [ ] Team trained on runbook procedures

## Troubleshooting

### Secret Access Denied

```bash
# Check IAM bindings
gcloud secrets get-iam-policy SECRET_NAME

# Grant access
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT_EMAIL" \
  --role="roles/secretmanager.secretAccessor"
```

### Application Can't Fetch Secrets

```python
# Add debugging (but don't log secret values)
import logging
logging.basicConfig(level=logging.DEBUG)

from secrets_util import get_secret
secret = get_secret('my-secret', fallback_env='FALLBACK')
```

### Audit Logs Not Showing

```bash
# Ensure Data Access audit logs are enabled
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --format='table(bindings.role)'
```

## Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Firebase Functions Documentation](https://firebase.google.com/docs/functions)
- [IAM Best Practices](https://cloud.google.com/iam/docs/best-practices-for-using-and-managing-service-accounts)
