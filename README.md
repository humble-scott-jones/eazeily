# Togetherly (dev)

Run dev server:
```bash
source .venv/bin/activate
PORT=5001 python3 app.py
```

Run tests:
```bash
source .venv/bin/activate
PYTHONPATH=. pytest -q
# or run the helper script
./run_tests.sh
```

Run UI smoke tests (requires server running on port 5001). These are gated so they don't run by default during local development. Set the env var RUN_UI_SMOKE=1 to enable them.
```bash
# run unit tests only
PYTHONPATH=. pytest -q

# run UI smoke tests
RUN_UI_SMOKE=1 PYTHONPATH=. pytest -q
```

## Supported Industries

Togetherly supports the following industries with tailored content templates, hashtags, and tone:

- 🏡 Realtor / Real Estate
- 🍽️ Restaurant / Café
- 🛍️ Retail / Boutique
- 💪 Fitness / Wellness
- 🎨 Artisan / Maker
- 🧭 Coach / Consultant
- 🤝 Nonprofit / Community
- 🛠️ Home Services
- 🩺 Healthcare
- ⛪ Church
- ✨ Other / Custom

Each industry includes:
- Industry-specific suggested keywords
- Customized content pillars and templates
- Platform-specific post formats
- Reel/video content styles tailored to the industry

Industry configurations are located in `/static/content/config.json`.

## Production Launch Checklist

Togetherly includes a comprehensive production launch checklist with prioritized, actionable items and GitHub issue templates.

📋 **[View the Launch Checklist](LAUNCH_CHECKLIST.md)**

The checklist includes:
- **17 must-have items** for safe production launch (security, monitoring, deployment, etc.)
- **13 nice-to-have items** for post-launch enhancement
- Ready-to-use GitHub issue templates for each item
- Sprint planning guidance and burn-down strategy
- Clear acceptance criteria and implementation tasks

To create launch tracking issues:
1. Go to **Issues → New Issue**
2. Select the appropriate launch template
3. Fill in any additional context
4. Add to your project board

## Automated Feedback Processing

Togetherly includes an automated system for processing user feedback into GitHub issues. When users submit feedback through the application, it can be automatically:
- Formatted into clear, structured GitHub issues using AI
- Tagged with appropriate labels
- Assigned to the team
- Logged for audit purposes

See [.github/README.md](.github/README.md) for complete documentation on the feedback automation system.

### Quick Start

To send feedback programmatically:

```python
import requests
from datetime import datetime

url = "https://api.github.com/repos/humble-scott-jones/togetherly/dispatches"
payload = {
    "event_type": "user_feedback",
    "client_payload": {
        "feedback": "User feedback text here...",
        "user_email": "user@example.com",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
}
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
requests.post(url, json=payload, headers=headers)
```
