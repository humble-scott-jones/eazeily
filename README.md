# Togetherly (dev)

## 🔒 Security & Secrets Management

**IMPORTANT**: Before deploying to production, review our security documentation:
- [Secrets Management Guide](docs/SECRETS_MANAGEMENT.md) - How to securely store and access secrets
- [Secrets Rotation Runbook](docs/SECRETS_ROTATION_RUNBOOK.md) - Procedures for rotating and revoking secrets
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) - Production deployment with Google Cloud Secret Manager

⚠️ **Never commit secrets to version control!** Use `.env` for local development only (already gitignored).

## Local Development Setup

Run dev server:
```bash
# Copy example environment file
cp .env.example .env
# Edit .env with your test credentials (use test keys only!)

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
