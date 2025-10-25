# Togetherly

AI-powered social media content generation that sounds like you.

## Development Setup

### Prerequisites
- Python 3.10+
- pip

### Installation

1. Clone the repository
2. Create a virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and configure your environment variables

### Running the Development Server

```bash
source .venv/bin/activate
PORT=5001 python3 app.py
```

The application will be available at `http://localhost:5001`

## Testing

### Run all tests:
```bash
source .venv/bin/activate
PYTHONPATH=. pytest -q
# or use the helper script
./run_tests.sh
```

### Run UI smoke tests:
UI smoke tests require the server to be running on port 5001. They are gated by default.

```bash
# run unit tests only
PYTHONPATH=. pytest -q

# run UI smoke tests (requires server running)
RUN_UI_SMOKE=1 PYTHONPATH=. pytest -q
```

## Project Structure

```
togetherly/
├── app.py              # Main Flask application
├── generator.py        # Content generation logic
├── templates/          # HTML templates
│   ├── index.html      # Main application UI
│   ├── landing.html    # Marketing landing page
│   ├── pricing.html    # Pricing page
│   ├── account.html    # User account page
│   └── admin.html      # Admin interface
├── static/             # Static assets (CSS, JS)
├── tests/              # Test suite
├── docs/               # Documentation
│   ├── PRODUCTION_READY.md      # Production readiness overview
│   ├── SECRETS_MANAGEMENT.md    # Secrets & security guide
│   ├── PRODUCTION_CHECKLIST.md  # Deployment checklist
│   └── ACCEPTANCE_TESTING.md    # Testing scenarios
└── requirements.txt    # Python dependencies
```

## Features

- **AI-Powered Content Generation**: Create social media posts with AI
- **Multi-Platform Support**: Instagram, LinkedIn, Twitter, Facebook
- **Brand Voice Customization**: Match your unique tone and style
- **Subscription Management**: Integrated with Stripe for payments
- **Admin Tools**: Reconciliation and management features

## Production Deployment

📖 **See [docs/PRODUCTION_READY.md](docs/PRODUCTION_READY.md) for complete production deployment guide**

Key documentation:
- **[Secrets Management](docs/SECRETS_MANAGEMENT.md)** - How to securely store production secrets
- **[Production Checklist](docs/PRODUCTION_CHECKLIST.md)** - Complete deployment checklist
- **[Acceptance Testing](docs/ACCEPTANCE_TESTING.md)** - Test scenarios for production validation

### Quick Production Setup

1. Choose a secrets management solution (Firebase, AWS, GCP, etc.)
2. Configure all required environment variables
3. Complete the pre-deployment checklist
4. Run acceptance tests in staging
5. Deploy following the production checklist
6. Monitor according to post-deployment guidelines

## Environment Variables

See `.env.example` for a complete list. Key variables:

- `SECRET_KEY` - Flask session secret
- `STRIPE_SECRET_KEY` - Stripe API secret key
- `STRIPE_PUBLISHABLE_KEY` - Stripe public key
- `STRIPE_WEBHOOK_SECRET` - Webhook signature verification
- `ADMIN_EMAILS` - Comma-separated admin email addresses
- `OPENAI_API_KEY` - Optional, for AI content generation

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests to ensure they pass
4. Submit a pull request

## License

Copyright © 2025 Togetherly. All rights reserved.

## Additional Resources

- [Stripe Integration Guide](README_STRIPE.md)
- [Production Documentation](docs/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Stripe API Docs](https://stripe.com/docs)
