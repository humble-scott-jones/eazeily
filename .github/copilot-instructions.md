# Swelly - GitHub Copilot Instructions

## Project Overview

Swelly is a Flask-based web application that helps small businesses and organizations generate social media content. It provides industry-specific content templates, customizable tones, and multi-platform support for creating engaging posts tailored to various business types.

### Core Purpose
Generate personalized social media posts for multiple industries (realtor, restaurant, retail, fitness, artisan, coach, nonprofit, home services, healthcare, church, and custom) with appropriate tone, keywords, and platform-specific formatting.

## Technology Stack

- **Backend**: Python 3.10+ with Flask 3.0.3
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Database**: SQLite3 (swelly.db)
- **Key Dependencies**:
  - Flask-Cors for CORS handling
  - OpenAI API (optional) for enhanced content generation
  - Stripe (optional) for payment processing
  - pytest for testing

## Architecture

### Application Structure
```
swelly/
├── app.py                    # Main Flask application with routes and business logic
├── generator.py              # Content generation logic (posts, captions, hashtags)
├── templates/                # Jinja2 HTML templates
│   ├── index.html           # Main content generation interface
│   ├── account.html         # User account/subscription management
│   ├── complete.html        # Post-checkout success page
│   └── admin.html           # Admin reconciliation interface
├── static/
│   ├── content/
│   │   ├── config.json      # Industry configurations, tones, platforms
│   │   └── flags.json       # Feature flags
│   ├── app.js               # Main frontend application logic
│   ├── complete.js          # Checkout completion handling
│   └── styles.css           # Application styles
├── tests/                    # Comprehensive test suite
└── scripts/                  # Utility scripts
```

### Key Components

1. **Content Generation** (`generator.py`):
   - Industry-specific content pillars (Educational, Behind-the-Scenes, Testimonial, etc.)
   - Platform-specific hints (Instagram, Facebook, LinkedIn, TikTok, Twitter)
   - Customizable tones (friendly, professional, playful, inspirational)
   - Hashtag generation based on industry and keywords

2. **User Management** (`app.py`):
   - SQLite database for user accounts and subscriptions
   - Password hashing with werkzeug.security
   - Session-based authentication
   - Email-based admin authorization

3. **Subscription System** (optional):
   - Stripe integration for payment processing
   - Webhook handling for subscription events
   - Admin reconciliation interface

4. **Feature Flags** (`static/content/flags.json`):
   - Control feature availability (e.g., `openai_chat`, `subscriptions`)
   - Frontend reads flags to show/hide features dynamically

## Development Workflow

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start development server
PORT=5001 python3 app.py
```

### Testing

```bash
# Run all tests (unit tests only by default)
PYTHONPATH=. pytest -q

# Or use the helper script
./run_tests.sh

# Run UI smoke tests (requires server running on port 5001)
RUN_UI_SMOKE=1 PYTHONPATH=. pytest -q
```

**Important Testing Notes**:
- UI smoke tests are gated by `RUN_UI_SMOKE` environment variable
- Tests use pytest fixtures from `tests/conftest.py`
- Each test gets an isolated temporary SQLite database
- All tests should be independent and idempotent

### CI/CD
GitHub Actions workflow (`.github/workflows/ci.yml`) runs tests on Python 3.10 and 3.11 for every push and PR.

## Coding Standards

### Python Code Style
- Follow PEP 8 conventions
- Use type hints where appropriate (see `generator.py` for examples)
- Keep functions focused and single-purpose
- Use descriptive variable names
- Database connections: Always use context managers or ensure proper cleanup

### Flask Patterns
- Use `g` object for request-scoped database connections
- Always register teardown handlers for resource cleanup
- Protect admin routes with email-based authorization checks
- Return JSON responses with appropriate status codes
- Handle optional dependencies gracefully (see OpenAI and Stripe imports in `app.py`)

### Frontend Code Style
- Use vanilla JavaScript (no frameworks)
- Keep JavaScript modular with clear function responsibilities
- Use `fetch` for API calls with proper error handling
- Maintain consistent indentation (2 spaces for JS/HTML/CSS)

### Database Patterns
- Use parameterized queries to prevent SQL injection
- Access database through `get_db()` function
- Use `row_factory = sqlite3.Row` for named column access
- Include proper indexes for performance

### Testing Patterns
- Use pytest fixtures for test setup
- Isolate tests with temporary databases
- Use descriptive test names that explain what is being tested
- Test both success and error cases
- Mark UI tests with `@pytest.mark.ui` decorator
- Keep test data minimal and focused

## Configuration

### Environment Variables
- `SECRET_KEY`: Flask session secret (required)
- `OPENAI_API_KEY`: Optional, enables OpenAI-powered content generation
- `STRIPE_SECRET_KEY`: Optional, enables Stripe payment processing
- `STRIPE_PUBLISHABLE_KEY`: Frontend Stripe key
- `STRIPE_TEST_PRICE_ID`: Price ID for test subscriptions
- `STRIPE_WEBHOOK_SECRET`: Stripe webhook signature verification
- `ADMIN_EMAILS`: Comma-separated list of admin email addresses
- `FLASK_ENV`: Set to 'development' for debug mode
- `PORT`: Server port (default: 5001)

### Configuration Files
- `.env.example`: Template for environment variables
- `static/content/config.json`: Industry configurations (editable)
- `static/content/flags.json`: Feature flags (editable)

## Industry Configuration

When adding or modifying industries in `static/content/config.json`:
1. Each industry needs: `key`, `icon`, `label`, `suggested_keywords`, `note_placeholder`
2. Add corresponding questions array with appropriate fields
3. Include `reel_style` options for video content suggestions
4. Update README.md if adding major new industry types

## Common Development Tasks

### Adding a New Industry
1. Add entry to `industries` array in `config.json`
2. Add questions for that industry in `questions` object
3. Test content generation with the new industry
4. Update tests if needed (see `test_church_industry.py` for example)

### Modifying Content Generation
- Main logic in `generator.py` functions: `make_caption()`, `generate_posts()`
- Platform hints in `PLATFORM_HINTS` dictionary
- Content pillars in `PILLARS_BY_DEFAULT` list
- Test changes with various industry/platform/tone combinations

### Adding New Routes
1. Add route handler in `app.py`
2. Use appropriate HTTP methods (GET for retrieval, POST for creation/updates)
3. Implement authentication checks if needed
4. Return JSON for API endpoints, render templates for pages
5. Add corresponding tests in `tests/` directory

### Database Schema Changes
1. Update `init_db()` function in `app.py`
2. Consider migration strategy for existing databases
3. Update test fixtures if schema changes affect tests
4. Document schema changes in commit messages

## Security Considerations

- **Passwords**: Always use `generate_password_hash` and `check_password_hash`
- **SQL Injection**: Always use parameterized queries
- **Session Security**: Ensure `SECRET_KEY` is strong and not committed
- **API Keys**: Never commit API keys; use environment variables
- **Admin Access**: Verify admin status before allowing sensitive operations
- **CORS**: Configured via Flask-Cors; review settings if adding new origins
- **Stripe Webhooks**: Verify webhook signatures with `STRIPE_WEBHOOK_SECRET`

## Best Practices for AI Assistance

### When Making Changes
1. **Understand First**: Read existing code patterns before modifying
2. **Minimal Changes**: Make the smallest changes necessary to achieve the goal
3. **Test Early**: Run tests frequently during development
4. **Follow Patterns**: Match existing code style and structure
5. **Preserve Functionality**: Don't break working code unless fixing a bug

### When Adding Features
1. Check if similar functionality exists and follow its pattern
2. Add tests alongside feature implementation
3. Update configuration files if adding new options
4. Document significant changes in code comments if complexity requires it

### When Debugging
1. Run tests to identify failures: `PYTHONPATH=. pytest -q -v`
2. Check application logs and Flask debug output
3. Verify environment variables are set correctly
4. Use SQLite CLI to inspect database state if needed: `sqlite3 swelly.db`

### When Reviewing Code
1. Ensure tests pass: `./run_tests.sh`
2. Verify no credentials or secrets are committed
3. Check that changes align with existing patterns
4. Confirm error handling is appropriate
5. Validate that UI changes work across supported industries/platforms

## Resources

- Flask Documentation: https://flask.palletsprojects.com/
- pytest Documentation: https://docs.pytest.org/
- Stripe API: https://stripe.com/docs/api (if using payments)
- OpenAI API: https://platform.openai.com/docs (if using AI generation)

## Support and Contribution

- Keep changes focused and scoped to the issue at hand
- Write clear commit messages describing what and why
- Ensure all tests pass before considering work complete
- Preserve existing functionality unless explicitly fixing bugs
