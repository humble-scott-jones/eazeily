# Togetherly

A social media content generation platform that helps small businesses create engaging content for their industries.

## Quick Start

### Development Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
PORT=5001 python3 app.py
```

### Running Tests

```bash
# Run all tests
pytest -q

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_generator.py -v

# Run UI smoke tests (requires server running on port 5001)
RUN_UI_SMOKE=1 pytest tests/test_ui_smoke.py
```

See [TESTING.md](TESTING.md) for comprehensive testing guide.

## Supported Industries
This document explains how to set up and run Togetherly locally, run tests (including reproducing CI artifact collection), install optional Playwright tooling, and troubleshoot common issues.

## Quickstart

If you just want to boot the dev server and click through the UI, follow these macOS/zsh-friendly steps:

1. Create and activate the virtual environment (only required once per clone):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   .venv/bin/python -m pip install --upgrade pip
   .venv/bin/python -m pip install -r requirements.txt
   ```

2. Start the server in the background (writes stdout/stderr to `.dev_server.log` and PID to `.dev_server.pid`):

   ```bash
   lsof -ti :5001 | xargs -r kill -9 || true
   PORT=5001 FLASK_ENV=development ALLOW_DEV_DEBUG=1 ./.venv/bin/python app.py > .dev_server.log 2>&1 & echo $! > .dev_server.pid
   tail -n +1 .dev_server.log | sed -n '1,120p'
   cat .dev_server.pid
   ```

3. Sanity-check the dev ping endpoint:

   ```bash
   curl -i http://127.0.0.1:5001/__dev__/ping
   # expected: HTTP/1.1 200 OK and body 'pong'
   ```

Once you are done, stop the server with `kill "$(cat .dev_server.pid)"`.

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

## OpenAI integration: ChatGPT vs API

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

New coverage:
- `tests/test_api_generate_payload.py` validates that `/api/generate` forwards tone, platforms, goals, and both keyword sets to the underlying generator.
Industry configurations are located in `/static/content/config.json`.

## Documentation

### For Developers
- **[TESTING.md](TESTING.md)** - Testing strategy, test pyramid, and coverage requirements
- **[SECURITY.md](SECURITY.md)** - Security best practices and guidelines
- **README_STRIPE.md** - Stripe integration documentation

### For Operations
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment procedures, rollback, and database migrations
- **[MONITORING.md](MONITORING.md)** - Monitoring, logging, alerting, and observability
- **[INCIDENT_RESPONSE.md](INCIDENT_RESPONSE.md)** - Incident response procedures and playbooks

## Production Considerations

### Environment Variables

Required for production:
```bash
SECRET_KEY=<strong-random-secret>
DATABASE_URL=<postgresql-connection-string>
STRIPE_SECRET_KEY=<stripe-api-key>
STRIPE_WEBHOOK_SECRET=<stripe-webhook-secret>
OPENAI_API_KEY=<openai-api-key>
ADMIN_EMAILS=<comma-separated-admin-emails>
FLASK_ENV=production
```

See `.env.example` for complete list.

### Health Check

The application provides a health check endpoint for monitoring:
```bash
curl http://localhost:5001/health
```

Returns:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-10-26T14:00:00Z",
  "checks": {
    "database": "connected",
    "stripe": "configured",
    "openai": "configured"
  }
}
```

### Security

- HTTPS required in production
- Session cookies are secure (HTTPOnly, Secure, SameSite)
- Passwords hashed with PBKDF2-SHA256
- SQL injection prevention via parameterized queries
- CSRF protection enabled
- Rate limiting recommended

See [SECURITY.md](SECURITY.md) for comprehensive security guide.

### Monitoring

Key metrics to monitor:
- Request rate and response time
- Error rate (< 0.1% target)
- Database connection pool utilization
- External API latency (Stripe, OpenAI)
- Resource usage (CPU, memory, disk)

See [MONITORING.md](MONITORING.md) for detailed monitoring setup.

## CI/CD

### GitHub Actions Workflows

- **CI (Pull Requests):** Unit tests, integration tests, coverage, linting, security scans
- **E2E Tests:** End-to-end tests on main/staging branches
- **Security:** Dependency vulnerability scanning

### Test Coverage

Current coverage: 63% (target: 80%)

Critical paths require 90%+ coverage:
- Authentication and authorization
- Payment processing
- Content generation

## Performance

### Load Testing

Use Locust for performance testing:
```bash
cd tests/performance
locust -f locustfile.py --host=http://localhost:5001
```

Performance targets:
- p95 response time < 2 seconds
- 100 requests/second throughput
- < 0.1% error rate under normal load

See `tests/performance/README.md` for detailed guide.

## Contributing

1. Create feature branch from `main`
2. Write tests for new functionality
3. Ensure all tests pass and coverage maintained
4. Follow security checklist in PR template
5. Submit PR with comprehensive description
6. Address review feedback
7. Merge after approval and passing CI

See `.github/PULL_REQUEST_TEMPLATE.md` for PR checklist.

## Architecture

- **Backend:** Python Flask
- **Database:** SQLite (dev), PostgreSQL (production)
- **Payment:** Stripe
- **AI:** OpenAI API
- **Frontend:** Server-side rendered templates

## License

[Add license information]

## Support

For security issues, see [SECURITY.md](SECURITY.md) for responsible disclosure.

For other issues, open a GitHub issue or contact [support contact].

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
