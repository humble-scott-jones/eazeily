# Secrets Rotation and Revocation Runbook

## Overview

This runbook provides step-by-step procedures for rotating and revoking secrets in emergency and routine scenarios.

## Rotation Schedule

| Secret Type | Rotation Frequency | Last Rotated | Next Rotation |
|------------|-------------------|--------------|---------------|
| Stripe API Keys | 90 days | TBD | TBD |
| Flask SECRET_KEY | 180 days | TBD | TBD |
| OpenAI API Key | 90 days | TBD | TBD |
| Stripe Webhook Secret | On compromise | TBD | As needed |
| Admin Passwords | 60 days | TBD | TBD |

## Routine Rotation Procedures

### 1. Rotating Stripe API Keys

**Impact**: Brief downtime during rotation (< 5 minutes)

**Steps**:

1. **Generate new key in Stripe Dashboard**
   - Go to https://dashboard.stripe.com/apikeys
   - Click "Create secret key"
   - Note the new key (it will only be shown once)

2. **Store new key in Secret Manager**
   ```bash
   # Create new version of secret
   echo -n "sk_live_NEW_KEY" | gcloud secrets versions add stripe-secret-key \
     --data-file=-
   ```

3. **Update application configuration**
   - For Cloud Run: Deploy with new secret version
   - For Firebase Functions: Redeploy functions
   ```bash
   gcloud run services update togetherly \
     --update-secrets=STRIPE_SECRET_KEY=stripe-secret-key:latest
   ```

4. **Verify new key works**
   ```bash
   # Test the API with new key
   curl https://api.stripe.com/v1/customers \
     -u sk_live_NEW_KEY: \
     -d limit=1
   ```

5. **Disable old key in Stripe Dashboard**
   - Wait 24 hours to ensure no services are using old key
   - Roll back the key in Stripe dashboard

6. **Update rotation schedule** (in this document)

### 2. Rotating Flask SECRET_KEY

**Impact**: All users will be logged out

**Steps**:

1. **Generate new secret key**
   ```python
   import secrets
   new_key = secrets.token_urlsafe(32)
   print(new_key)
   ```

2. **Store in Secret Manager**
   ```bash
   echo -n "NEW_SECRET_KEY" | gcloud secrets versions add flask-secret-key \
     --data-file=-
   ```

3. **Deploy with new key**
   ```bash
   gcloud run services update togetherly \
     --update-secrets=SECRET_KEY=flask-secret-key:latest
   ```

4. **Notify users** that they will need to log in again

5. **Update rotation schedule**

### 3. Rotating OpenAI API Key

**Impact**: Content generation temporarily unavailable during rotation

**Steps**:

1. **Create new API key in OpenAI**
   - Go to https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key

2. **Store in Secret Manager**
   ```bash
   echo -n "NEW_OPENAI_KEY" | gcloud secrets versions add openai-api-key \
     --data-file=-
   ```

3. **Deploy application**
   ```bash
   gcloud run services update togetherly \
     --update-secrets=OPENAI_API_KEY=openai-api-key:latest
   ```

4. **Verify functionality**
   - Test content generation feature
   - Check application logs for errors

5. **Revoke old key in OpenAI dashboard**

6. **Update rotation schedule**

### 4. Rotating Stripe Webhook Secret

**Impact**: Webhook events will fail until rotation is complete

**Steps**:

1. **Create new webhook endpoint with new secret** (if supported)
   - OR rotate secret for existing endpoint in Stripe Dashboard

2. **Store new secret**
   ```bash
   echo -n "whsec_NEW_SECRET" | gcloud secrets versions add stripe-webhook-secret \
     --data-file=-
   ```

3. **Deploy application**
   ```bash
   gcloud run services update togetherly \
     --update-secrets=STRIPE_WEBHOOK_SECRET=stripe-webhook-secret:latest
   ```

4. **Test webhook**
   - Send test webhook from Stripe Dashboard
   - Verify signature validation succeeds

5. **Remove old webhook endpoint** (if applicable)

6. **Update rotation schedule**

## Emergency Revocation Procedures

### When to Use Emergency Procedures

- Secret detected in public repository
- Unauthorized access detected in audit logs
- Team member with secret access leaves the company
- Security vulnerability requires immediate action

### Emergency Rotation Checklist

⚠️ **Act quickly but deliberately. Follow these steps in order:**

1. **[ ] Assess the situation**
   - What secret was compromised?
   - How was it exposed?
   - What systems are affected?
   - Is there evidence of unauthorized use?

2. **[ ] Immediately revoke compromised secret**
   
   For Stripe:
   ```bash
   # Disable key in Stripe dashboard immediately
   # Dashboard: https://dashboard.stripe.com/apikeys
   ```
   
   For Google Cloud Secret Manager:
   ```bash
   # Disable all versions of the secret
   gcloud secrets versions disable VERSION_ID --secret=SECRET_NAME
   ```

3. **[ ] Generate and deploy new secret** (follow rotation procedures above, but expedited)

4. **[ ] Review audit logs**
   ```bash
   # Check for unauthorized access
   gcloud logging read "resource.type=secretmanager.googleapis.com/Secret \
     AND resource.labels.secret_id=SECRET_NAME" \
     --limit 100 \
     --format json
   ```

5. **[ ] Investigate impact**
   - Check application logs for anomalies
   - Review Stripe/payment transactions for fraud
   - Check user accounts for unauthorized access

6. **[ ] Notify stakeholders**
   - Security team
   - Management (if significant)
   - Customers (if their data was affected)

7. **[ ] Document incident**
   - What happened
   - How it was detected
   - Actions taken
   - Lessons learned
   - Preventive measures

8. **[ ] Implement preventive measures**
   - Review access controls
   - Update pre-commit hooks
   - Enhance monitoring
   - Update team training

### Post-Incident Review Template

```markdown
# Security Incident Report: [YYYY-MM-DD]

## Incident Summary
- **Date/Time**: 
- **Detected By**: 
- **Affected Secrets**: 
- **Severity**: Critical / High / Medium / Low

## Timeline
- [Time] Incident detected
- [Time] Secret revoked
- [Time] New secret deployed
- [Time] Service restored
- [Time] Investigation completed

## Root Cause
[Describe how the secret was compromised]

## Impact Analysis
- **Service Downtime**: X minutes
- **Data Exposure**: None / Limited / Significant
- **Financial Impact**: $X
- **User Impact**: X users affected

## Actions Taken
1. Revoked compromised secret at [time]
2. Deployed new secret at [time]
3. Reviewed audit logs
4. [Additional actions]

## Lessons Learned
- [What went well]
- [What could be improved]
- [Gaps in process]

## Preventive Measures
- [ ] [Action item 1]
- [ ] [Action item 2]
- [ ] [Action item 3]

## Follow-up Items
- [ ] Update rotation schedule
- [ ] Review access controls
- [ ] Update documentation
- [ ] Team training session
```

## GitHub Secret Scanning Response

If GitHub detects a secret in your repository:

1. **Acknowledge the alert immediately**
   - Go to Security > Secret scanning alerts

2. **Verify if it's a true positive**
   - Check if the secret is real or a false positive
   - Check if the secret is still active

3. **If true positive:**
   ```bash
   # Follow emergency revocation procedures above
   # Additionally, remove the secret from git history:
   
   # Using BFG Repo-Cleaner (recommended for large repos)
   bfg --replace-text passwords.txt
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   
   # OR using git-filter-repo
   git filter-repo --path-glob '*secret*' --invert-paths
   ```

4. **Force push cleaned history** (coordinate with team!)
   ```bash
   git push --force --all
   git push --force --tags
   ```

5. **Resolve the GitHub alert** and document the response

## Automated Monitoring

### Set up Cloud Monitoring Alerts

```bash
# Alert when secret is accessed from unexpected IP
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Unusual Secret Access" \
  --condition-display-name="Secret accessed from new location" \
  --condition-filter='resource.type="secretmanager.googleapis.com/Secret"'
```

### Regular Audit Log Review

Schedule weekly reviews of secret access:

```bash
#!/bin/bash
# scripts/audit-secrets.sh

gcloud logging read \
  "resource.type=secretmanager.googleapis.com/Secret \
   AND timestamp>\"$(date -u -d '7 days ago' '+%Y-%m-%dT%H:%M:%SZ')\"" \
  --format=json \
  | jq -r '.[] | [.timestamp, .resource.labels.secret_id, .protoPayload.authenticationInfo.principalEmail] | @csv'
```

## Contact Information

### On-Call Rotation
- Primary: [Name] - [Phone/Email]
- Secondary: [Name] - [Phone/Email]

### Escalation Path
1. Security Team Lead - [Contact]
2. CTO - [Contact]
3. CEO - [Contact]

### External Contacts
- **Stripe Support**: https://support.stripe.com
- **Google Cloud Support**: [Your support case URL]
- **OpenAI Support**: https://help.openai.com

## Useful Commands Reference

```bash
# List all secrets
gcloud secrets list

# View secret versions
gcloud secrets versions list SECRET_NAME

# Access a secret
gcloud secrets versions access latest --secret=SECRET_NAME

# Create a new secret version
echo -n "NEW_VALUE" | gcloud secrets versions add SECRET_NAME --data-file=-

# Disable a secret version
gcloud secrets versions disable VERSION_ID --secret=SECRET_NAME

# View who has access to a secret
gcloud secrets get-iam-policy SECRET_NAME

# View audit logs for a specific secret
gcloud logging read "resource.labels.secret_id=SECRET_NAME" --limit=50

# Test Stripe API key
curl https://api.stripe.com/v1/customers -u YOUR_KEY: -d limit=1
```

## Checklist for New Team Members

When someone joins the team:
- [ ] Grant appropriate Secret Manager IAM roles
- [ ] Add to on-call rotation
- [ ] Review this runbook with them
- [ ] Test their access to secrets
- [ ] Add their contact info to this document

When someone leaves:
- [ ] Remove Secret Manager IAM roles immediately
- [ ] Rotate all secrets they had access to (within 24 hours)
- [ ] Remove from on-call rotation
- [ ] Review their recent secret access in audit logs
- [ ] Update contact information in this document
