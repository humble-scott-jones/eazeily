# Togetherly (dev)

## Quick Links
- 📖 **[User Journey Documentation](docs/user-journey.md)** - Complete end-to-end flow from profile setup through content generation
- 🚀 [Launch Checklist](LAUNCH_CHECKLIST.md)
- 🔧 [Testing Guide](TESTING.md)
- 🔐 [Security Guide](SECURITY.md)

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
# Togetherly — development guide

This document explains how to set up and run Togetherly locally, run tests (including reproducing CI artifact collection), install optional Playwright tooling, and troubleshoot common issues.

## Prerequisites (macOS)

- Python 3.10+ (use pyenv if you need multiple versions)
- Git
- (Optional) Stripe CLI for sending webhook events locally

All commands below assume you run them from the repository root.

## 1) Create a reproducible virtual environment

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
```

Activate the venv when running commands interactively:

```bash
source .venv/bin/activate
```

## 2) Environment variables

Create a `.env` (or export these in your shell). Example minimal set:

```bash
FLASK_ENV=development
ALLOW_DEV_DEBUG=1
PORT=5001
STRIPE_PUBLISHABLE_KEY=pk_test_YOUR_KEY
STRIPE_SECRET_KEY=sk_test_YOUR_KEY
STRIPE_PRICE_ID=price_test_YOUR_PRICE_ID
REELS_QUOTA_MONTHLY=5
```

Notes:
- `STRIPE_PRICE_ID` is the canonical price env var. Some code may still fall back to `STRIPE_TEST_PRICE_ID`.
- Keep real production secrets in your CI/host provider and out of version control.

Load `.env` into your shell (or use `direnv`) before running the server.

### GitHub feedback automation

To automatically turn in-product feedback into GitHub issues, add the following secrets to your `.env` (or hosting provider) once you enable the Settings → Feedback form:

```bash
GITHUB_FEEDBACK_TOKEN=ghp_xxx      # PAT with "repo" scope
GITHUB_FEEDBACK_REPO=owner/name    # e.g. humble-scott-jones/swelly
GITHUB_FEEDBACK_TEMPLATE_GENERAL=user-feedback   # optional override
GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN=thumbs-down  # optional override
```

Missing env vars simply disable the GitHub API call while still saving the feedback locally so you can develop without a PAT.

### Priority 0 runbook & smoke test

- 📘 `docs/runbooks/priority0.md` — step-by-step guide for wiring secrets, enabling branch protection, and running feedback smoke tests.
- 🧪 `scripts/feedback_smoke.sh` — posts a thumbs-down and Settings feedback payload so you can verify GitHub issues are created end-to-end (pass `--help` for usage).

## 3) Install Playwright (optional but recommended for e2e)

Playwright is optional. Install and download browsers if you plan to run browser tests or capture screenshots.

```bash
.venv/bin/python -m pip install playwright
.venv/bin/python -m playwright install --with-deps
```

CI installs Playwright and browsers if Playwright tests are enabled.

## 4) Linting

Run `flake8` locally (CI runs a lint step):

```bash
.venv/bin/python -m pip install flake8
.venv/bin/python -m flake8
```

Fix any errors flagged by flake8. We keep flake8 non-blocking in CI by default; make it strict if you want it to fail builds.

## 5) Start the dev server

With the `.venv` active and env vars loaded, run:

```bash
PORT=5001 FLASK_ENV=development ALLOW_DEV_DEBUG=1 .venv/bin/python app.py
```

Sanity-check endpoint:

```bash
curl http://127.0.0.1:5001/__dev__/ping
# expected: a simple dev response (e.g. 'pong')
```

## 6) Useful dev endpoints

- `GET /__dev__/create_user` — dev helper to create a test user (dev mode only)
- `GET /api/current_user` — returns the current session user
- `POST /api/profile` — persist profile details used by the generator
- `POST /api/generate` — request content generation (reels will be gated to paid users)
- `GET /api/stripe-price` — returns authoritative Stripe price metadata for paywall copy

### Generation task registry & aliases

- All dashboard tiles use `POST /api/generate` (alias: `POST /api/generate/<task_type>`).
- Supported `task_type` values: `post`, `caption`, `script`, `email`, `proposal`, `ad`, `review`, `blog`, `newsletter`.
- Task definitions (role, prompt template, platform requirement) live in `services/task_registry.py` and are consumed by `VoiceEngine`.
- Validation: `topic` required for all; `platform` required for `post`. Missing API key returns 503 with `error.code = "missing_api_key"`.
- If the caller has no saved profile, responses include `redirect: "/onboarding"` so the UI can nudge profile setup.

## 7) Running tests (pytest) — reproduce CI behavior

The CI collects a junit xml and captures logs. Replicate that locally:

```bash
# ensure test deps are installed
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install pytest

# run tests with junit output and capture console to a log file
.venv/bin/python -m pytest -q --maxfail=1 --junitxml=pytest-report.xml 2>&1 | tee pytest.log
```

After this runs you'll have `pytest-report.xml` and `pytest.log` at repo root (these are the same artifacts the CI uploads).

Notes:
- Unit tests mock Stripe where appropriate; integration tests that call Stripe require test keys.

## 8) Running Playwright tests (optional)

If you add Playwright tests, run them after installing Playwright and browsers:

```bash
# example: run playwright tests directory
.venv/bin/python -m pytest tests/playwright -q
```

Playwright typically writes artifacts under `playwright-report/`. The CI can be configured to upload that directory as artifacts.

## 9) Reproducing CI locally (summary)

CI performs these high-level steps:

1. Install Python deps
2. Install Playwright & browsers (optional)
3. Run flake8 (lint)
4. Run pytest with `--junitxml=pytest-report.xml` and capture stdout to `pytest.log`
5. Upload artifacts (junit xml, pytest log, Playwright artifacts)

To reproduce, run the commands in sections 1, 3, and 7 in sequence.

## 10) Troubleshooting

- Port already in use: `lsof -i :5001 -P -n` then `kill <pid>`
- Tests failing due to Stripe: ensure `STRIPE_SECRET_KEY` and `STRIPE_PUBLISHABLE_KEY` are set for integration tests or use the unit tests which mock Stripe
- Playwright missing deps: run `playwright install --with-deps` and follow Playwright error hints for system libraries

## 11) Notes & next steps

- Standardize documentation and `.env.example` to use `STRIPE_PRICE_ID` going forward.
- Consider enabling Playwright tests in CI if you want e2e coverage and artifact collection on failures.
- Tighten flake8 rules in CI and fix remaining lint issues.

If anything in these instructions doesn't work on your machine, paste the failing command and its output and I'll help fix it.

## AI Integration: Google Gemini API (Required)

**Important**: Eazeily now uses Google Gemini for AI-powered features including content generation and brand voice assistance.

### Quick Setup

1. Get an API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Add to your `.env` file:
   ```bash
   GENAI_API_KEY=your_api_key_here
   ```
3. Verify setup:
   ```bash
   python3 scripts/test_gemini_api.py
   ```

**Features that require Gemini API:**
- Content generation (social posts, emails, ads, etc.)
- AI voice helper (interactive brand voice builder)
- Brand voice analysis

**📖 Full setup guide**: See [docs/GEMINI_SETUP.md](docs/GEMINI_SETUP.md) for detailed instructions, troubleshooting, and best practices.

**Free tier**: Gemini offers a free tier with 15 requests/minute - sufficient for development and testing.

## OpenAI integration: ChatGPT vs API (Optional)

You don’t need a ChatGPT subscription in the app. Togetherly uses the OpenAI API when configured. If an API key isn’t set, it falls back to the built‑in generator.

- Set OPENAI_API_KEY in your environment to enable API-backed generation.
- Optionally set OPENAI_MODEL (defaults to "gpt-4o-mini").

Behavior:
- With OPENAI_API_KEY: The server sends a structured JSON-only request with your industry, tone, goals, platforms, and keywords. The system prompt is tuned for influencer-quality copy with platform nuances, a strong hook/CTA for reels, and natural keyword usage.
- Without OPENAI_API_KEY: The local generator produces consistent posts without calling the internet.

Troubleshooting:
- If the OpenAI call fails or returns unusable data, the app automatically falls back to the local generator so you’re never blocked.

## Content pack

The “content pack” is the versioned set of static content used by the wizard:

- static/content/config.json — industries, tones, platforms, industry questions, and pricing copy
- static/content/flags.json — optional feature flags (e.g., showing the 7‑day button)
- GET /api/content — returns { version, flags } for surfacing in the UI

You can change industries, suggested keywords, and questions by editing config.json. The UI shows the content pack version in the Settings card.

## Goals are multi-select

In step 2, “Goals” chips allow multi-selection (they’re stored in answers.goals). These are passed into the generator (and the OpenAI payload when enabled) to shape captions and reels toward those outcomes.

## Faster, clearer tests

Tips to keep tests actionable:

- Run unit tests only: `./run_tests.sh`
- Run UI smoke tests (requires local server on port 5001): `RUN_UI_SMOKE=1 ./run_tests.sh`
- Capture CI-style artifacts: `.venv/bin/python -m pytest -q --maxfail=1 --junitxml=pytest-report.xml 2>&1 | tee pytest.log`
- Helpful flags: append `--durations=10` to find slowest tests or use `-k` for targeted subsets.

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
New coverage:
- `tests/test_api_generate_payload.py` validates that `/api/generate` forwards tone, platforms, goals, and both keyword sets to the underlying generator.
Industry configurations are located in `/static/content/config.json`.

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
