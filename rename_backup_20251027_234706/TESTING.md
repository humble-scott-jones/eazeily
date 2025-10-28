# Testing Guide

## Test Pyramid

Togetherly follows the test pyramid approach to ensure comprehensive coverage while maintaining fast feedback loops:

```
      /\
     /E2E\         End-to-End Tests (slowest, highest confidence)
    /------\
   /  Int.  \      Integration Tests (medium speed)
  /----------\
 /   Unit     \    Unit Tests (fastest, most numerous)
/--------------\
```

### Unit Tests
**Purpose:** Test individual functions and modules in isolation  
**Location:** `tests/test_*.py`  
**Speed:** < 1 second per test  
**Coverage Target:** 80%+

Examples:
- `test_generator.py` - Content generation logic
- `test_profile_validation.py` - Input validation
- `test_auth.py` - Authentication helpers

**When to write:** For every new function or class with business logic

### Integration Tests
**Purpose:** Test interactions between components (database, APIs, services)  
**Location:** `tests/test_*_api.py`, `tests/test_webhook.py`  
**Speed:** 1-5 seconds per test

Examples:
- `test_checkout.py` - Stripe integration
- `test_webhook.py` - Webhook handling
- `test_reconcile.py` - Database operations

**When to write:** When testing component interactions, external APIs, or database operations

### End-to-End (E2E) Tests
**Purpose:** Test complete user flows through the application  
**Location:** `tests/test_end_to_end.py`, `tests/test_acceptance_api.py`  
**Speed:** 5-30 seconds per test

Examples:
- User registration → profile creation → content generation
- Subscription signup → payment → feature access

**When to write:** For critical user journeys and release validation

### UI Smoke Tests
**Purpose:** Quick validation that UI is functional  
**Location:** `tests/test_ui_smoke.py`  
**Speed:** Variable (requires running server)  
**Run with:** `RUN_UI_SMOKE=1 pytest`

**Note:** UI smoke tests are gated and require the server to be running on port 5001.

## Contract Tests
**Purpose:** Validate API contracts remain stable  
**Approach:** Use request/response validation against OpenAPI spec

For external APIs (Stripe, OpenAI):
- Mock responses for unit tests
- Use test mode/sandbox for integration tests
- Document expected request/response formats

## Running Tests

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run unit tests only (default)
pytest -q

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_generator.py -v

# Run tests matching pattern
pytest -k "test_auth" -v

# Run UI smoke tests (server must be running on port 5001)
RUN_UI_SMOKE=1 pytest tests/test_ui_smoke.py
```

### CI/CD
Tests run automatically on:
- **Pull Requests:** Unit + Integration tests (fast tests)
- **Main/Staging:** Unit + Integration + E2E tests
- **Pre-Production:** Full test suite including performance tests

## Coverage Requirements

- **Overall Coverage:** 80% minimum
- **Critical Paths:** 90% minimum (auth, payment, content generation)
- **New Code:** 85% minimum (enforced on PRs)

View coverage report:
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

## Test Data Management

### Test Fixtures
Defined in `tests/conftest.py`:
- `client`: Flask test client with isolated test database
- Temporary database per test for isolation

### Test Database
- Each test gets a fresh SQLite database in `tmp_path`
- No shared state between tests
- Clean slate for every test run

### Environment Variables
Test-specific configuration in `conftest.py`:
- `TESTING=True` - Disables external API calls
- Test secrets for Stripe, OpenAI mocked or use test mode

## Best Practices

1. **Isolation:** Each test should be independent and not rely on other tests
2. **Fast:** Keep unit tests under 1 second
3. **Deterministic:** Tests should produce same results every time
4. **Clear Names:** Use descriptive test names: `test_<what>_<when>_<expected>`
5. **Arrange-Act-Assert:** Structure tests clearly
   ```python
   def test_generate_posts_includes_company_name():
       # Arrange
       profile = {'company': 'Test Co', ...}
       
       # Act
       result = generate_posts(profile)
       
       # Assert
       assert 'Test Co' in result['posts'][0]['caption']
   ```

## Performance Testing

### Load Testing
**Tool:** Locust (or similar)  
**Scenarios:**
- Concurrent content generation requests
- High-traffic periods (10x normal load)
- Database query performance under load

**KPIs:**
- Response time: p95 < 2s for content generation
- Throughput: 100 requests/second
- Error rate: < 0.1% under normal load

**Schedule:**
- Before major releases
- Weekly on staging environment
- After infrastructure changes

### Baseline Metrics
Document baseline performance in `tests/performance/`:
- Average response times per endpoint
- Database query performance
- Memory usage patterns
- CPU utilization under load

## Continuous Testing

### Pre-commit
- Run linter/formatter
- Run fast unit tests (< 5 seconds total)

### Pull Request
- All unit tests must pass
- Coverage must meet threshold
- No new security vulnerabilities
- Integration tests pass

### Merge to Main
- Full test suite including E2E
- Performance regression tests
- Security scans

## Writing New Tests

1. **Identify test type:** Unit, Integration, or E2E?
2. **Create test file:** Follow naming convention `test_<module>.py`
3. **Use fixtures:** Leverage existing fixtures from `conftest.py`
4. **Add markers:** Use `@pytest.mark.ui` for gated tests
5. **Document:** Add docstring explaining test purpose
6. **Run locally:** Verify test passes in isolation and with full suite

## Troubleshooting

### Tests Fail Locally But Pass in CI
- Check Python version match (CI uses 3.10, 3.11)
- Verify all dependencies installed
- Check for system-specific file paths

### Slow Tests
- Profile tests: `pytest --durations=10`
- Move slow tests to integration/E2E category
- Consider mocking external services

### Flaky Tests
- Check for shared state between tests
- Look for timing issues (use proper waits, not sleeps)
- Ensure proper cleanup in teardown

## Future Improvements

- [ ] Add mutation testing (e.g., mutmut)
- [ ] Implement visual regression testing for UI
- [ ] Add API contract testing with Pact or similar
- [ ] Set up property-based testing with Hypothesis
- [ ] Implement chaos engineering tests for resilience
