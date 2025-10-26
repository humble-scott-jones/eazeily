#!/bin/bash
# Fetch secrets from Google Cloud Secret Manager
# Usage: ./scripts/fetch-secrets.sh [environment]
# Example: ./scripts/fetch-secrets.sh production > .env.production

set -euo pipefail

ENVIRONMENT="${1:-production}"
PROJECT_ID="${GCP_PROJECT_ID:-}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP_PROJECT_ID environment variable not set" >&2
  echo "Usage: GCP_PROJECT_ID=your-project-id ./scripts/fetch-secrets.sh [environment]" >&2
  exit 1
fi

echo "# Fetched from Google Cloud Secret Manager on $(date)" >&2
echo "# Environment: $ENVIRONMENT" >&2
echo "# Project: $PROJECT_ID" >&2
echo "" >&2

# Define secrets to fetch based on environment
if [ "$ENVIRONMENT" = "production" ]; then
  SECRETS=(
    "flask-secret-key:SECRET_KEY"
    "stripe-secret-key:STRIPE_SECRET_KEY"
    "stripe-publishable-key:STRIPE_PUBLISHABLE_KEY"
    "stripe-webhook-secret:STRIPE_WEBHOOK_SECRET"
    "stripe-price-id:STRIPE_TEST_PRICE_ID"
    "openai-api-key:OPENAI_API_KEY"
    "admin-emails:ADMIN_EMAILS"
  )
else
  # Staging or dev environments might have different secrets
  SECRETS=(
    "flask-secret-key-${ENVIRONMENT}:SECRET_KEY"
    "stripe-secret-key-${ENVIRONMENT}:STRIPE_SECRET_KEY"
    "stripe-publishable-key-${ENVIRONMENT}:STRIPE_PUBLISHABLE_KEY"
    "stripe-webhook-secret-${ENVIRONMENT}:STRIPE_WEBHOOK_SECRET"
    "stripe-price-id-${ENVIRONMENT}:STRIPE_TEST_PRICE_ID"
    "openai-api-key-${ENVIRONMENT}:OPENAI_API_KEY"
    "admin-emails-${ENVIRONMENT}:ADMIN_EMAILS"
  )
fi

# Fetch each secret
for secret_mapping in "${SECRETS[@]}"; do
  IFS=':' read -r secret_id env_var <<< "$secret_mapping"
  
  echo "Fetching $secret_id..." >&2
  
  # Try to fetch the secret
  if value=$(gcloud secrets versions access latest --secret="$secret_id" --project="$PROJECT_ID" 2>/dev/null); then
    echo "${env_var}=${value}"
  else
    echo "Warning: Could not fetch secret '$secret_id'. Skipping." >&2
  fi
done

echo "" >&2
echo "✓ Secrets fetched successfully" >&2
echo "⚠️  IMPORTANT: Never commit these secrets to version control!" >&2
