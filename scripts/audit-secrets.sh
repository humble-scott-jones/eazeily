#!/bin/bash
# Audit secret access from Google Cloud Secret Manager
# Usage: ./scripts/audit-secrets.sh [days_back]
# Example: ./scripts/audit-secrets.sh 7

set -euo pipefail

DAYS_BACK="${1:-7}"
PROJECT_ID="${GCP_PROJECT_ID:-}"

if [ -z "$PROJECT_ID" ]; then
  echo "Error: GCP_PROJECT_ID environment variable not set"
  echo "Usage: GCP_PROJECT_ID=your-project-id ./scripts/audit-secrets.sh [days_back]"
  exit 1
fi

echo "Fetching secret access logs for the last $DAYS_BACK days..."
echo "Project: $PROJECT_ID"
echo ""

# Calculate the timestamp for filtering
if [[ "$OSTYPE" == "darwin"* ]]; then
  # macOS
  START_TIME=$(date -u -v-${DAYS_BACK}d '+%Y-%m-%dT%H:%M:%SZ')
else
  # Linux
  START_TIME=$(date -u -d "${DAYS_BACK} days ago" '+%Y-%m-%dT%H:%M:%SZ')
fi

# Fetch audit logs
gcloud logging read \
  "resource.type=\"secretmanager.googleapis.com/Secret\" \
   AND timestamp>=\"$START_TIME\" \
   AND protoPayload.methodName=\"google.cloud.secretmanager.v1.SecretManagerService.AccessSecretVersion\"" \
  --project="$PROJECT_ID" \
  --format=json \
  --limit=1000 | jq -r '
    .[] | 
    {
      timestamp: .timestamp,
      secret: .resource.labels.secret_id,
      user: .protoPayload.authenticationInfo.principalEmail,
      ip: .protoPayload.requestMetadata.callerIp,
      method: .protoPayload.methodName
    } | 
    [.timestamp, .secret, .user, .ip] | 
    @csv
  ' | sort -r

echo ""
echo "✓ Audit log retrieval complete"
