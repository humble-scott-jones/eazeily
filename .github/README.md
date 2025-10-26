# User Feedback Automation

This directory contains the automated feedback processing system that converts user feedback into structured GitHub issues.

## Overview

The feedback automation system:
1. Receives user feedback via repository_dispatch webhook
2. Uses an LLM (OpenAI GPT-4) to format raw feedback into a clear GitHub issue
3. Creates the issue with appropriate labels and assignees
4. Logs all feedback processing for audit purposes

## How It Works

### Triggering Feedback Processing

Send a `repository_dispatch` event to trigger the automation:

```bash
curl -X POST \
  -H "Accept: application/vnd.github.v3+json" \
  -H "Authorization: token YOUR_GITHUB_TOKEN" \
  https://api.github.com/repos/humble-scott-jones/togetherly/dispatches \
  -d '{
    "event_type": "user_feedback",
    "client_payload": {
      "feedback": "I would love to see more customization options for post templates...",
      "user_email": "user@example.com",
      "timestamp": "2024-01-15T10:30:00Z"
    }
  }'
```

### Workflow Steps

1. **Checkout**: Gets the latest version of the repository
2. **Format Feedback**: Calls the LLM to convert raw feedback into structured content
3. **Create Audit Log**: Records the original feedback and formatted output
4. **Create Issue**: Creates a GitHub issue with the formatted content, labels, and assignee

### Configuration

Edit `.github/config/feedback-automation.yml` to configure:
- `require_review`: Whether to require manual review (adds "needs-review" label)
- `labels`: Default labels to apply to feedback issues
- `default_assignee`: Who to assign feedback issues to

### LLM Prompt Template

The prompt used to format feedback is in `.github/config/feedback-prompt.txt`. You can edit this file to customize how feedback is structured.

## Components

### Workflow File
- **Location**: `.github/workflows/feedback-automation.yml`
- **Trigger**: `repository_dispatch` with type `user_feedback`
- **Permissions**: Requires `issues: write` and `contents: read`

### Processing Script
- **Location**: `.github/scripts/format_feedback.py`
- **Purpose**: Formats feedback using OpenAI API
- **Fallback**: If API fails, uses simple text formatting

### Configuration Files
- **feedback-automation.yml**: Main configuration settings
- **feedback-prompt.txt**: LLM prompt template (editable)

### Audit Logs
- **Location**: `.github/audit-logs/`
- **Format**: JSON files with timestamp
- **Contents**: Original feedback, formatted output, metadata
- **Note**: These are committed automatically by the workflow

## Required Secrets

Add these to your GitHub repository secrets:

- `OPENAI_API_KEY`: Your OpenAI API key for LLM formatting

## Testing

### Test Locally

```bash
cd .github/scripts

# Test with sample feedback
python format_feedback.py \
  --feedback "Add dark mode support" \
  --user-email "test@example.com" \
  --output /tmp/test_output.json

# View the output
cat /tmp/test_output.json
```

### Test the Workflow

Trigger a test dispatch event using the GitHub CLI:

```bash
gh api repos/humble-scott-jones/togetherly/dispatches \
  -f event_type=user_feedback \
  -f client_payload[feedback]="Test feedback message" \
  -f client_payload[user_email]="test@example.com" \
  -f client_payload[timestamp]="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
```

## Integration Points

### From Application Code

To send feedback from your application, make a POST request to GitHub's repository_dispatch endpoint:

```python
import requests
from datetime import datetime

def send_feedback_to_github(feedback_text, user_email, github_token):
    """Send user feedback to GitHub for automated processing."""
    url = "https://api.github.com/repos/humble-scott-jones/togetherly/dispatches"
    
    payload = {
        "event_type": "user_feedback",
        "client_payload": {
            "feedback": feedback_text,
            "user_email": user_email,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {github_token}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 204
```

### From External Forms

If using external form services (Typeform, Google Forms, etc.), configure their webhooks to call a serverless function that transforms the data and sends it to the repository_dispatch endpoint.

## Rate Limiting

Consider implementing rate limiting to prevent abuse:
- Require CAPTCHA on public feedback forms
- Limit submissions per user/IP address
- Monitor the workflow runs for unusual patterns

## Maintenance

### Reviewing Feedback Issues

Issues created with the automation are labeled with:
- `feedback`: Marks as user feedback
- `triage`: Needs initial review
- `needs-review` (optional): Requires manual approval before general visibility

### Audit Log Management

Audit logs accumulate over time. Consider:
- Archiving old logs periodically
- Setting up log rotation
- Using logs for analytics about feedback patterns

### Prompt Tuning

Monitor the quality of generated issues and adjust the prompt template in `feedback-prompt.txt` as needed to improve:
- Title clarity and consistency
- Body structure and completeness
- Technical detail preservation

## Troubleshooting

### Workflow Not Triggering

- Verify the `repository_dispatch` event is being sent correctly
- Check repository permissions for the workflow
- Review GitHub Actions logs for errors

### LLM Formatting Issues

- Check that `OPENAI_API_KEY` secret is set correctly
- Review audit logs to see the LLM's raw output
- Fallback formatting will be used if LLM fails
- Adjust the prompt template if output quality is poor

### Issue Creation Failures

- Ensure the workflow has `issues: write` permission
- Verify the assignee exists and is valid
- Check that labels exist in the repository

## Security Considerations

- **API Keys**: Never commit API keys; use GitHub Secrets
- **Rate Limiting**: Implement to prevent abuse
- **Input Validation**: Feedback text is sanitized in the workflow
- **Audit Trail**: All feedback is logged for security review
- **Review Process**: Enable `require_review` for sensitive projects

## Future Enhancements

Potential improvements:
- [ ] Add sentiment analysis to prioritize feedback
- [ ] Automatic categorization based on feedback content
- [ ] Integration with project boards
- [ ] Email notifications to submitters
- [ ] Duplicate detection to prevent similar issues
- [ ] Multi-language support
- [ ] Custom LLM models per feedback category
