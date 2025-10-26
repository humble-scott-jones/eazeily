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

