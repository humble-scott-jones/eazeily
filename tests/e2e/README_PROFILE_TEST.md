# Profile Creation Playwright Test

## Overview

This test (`test_profile_creation.py`) was created to reproduce and document the "silent death click" issue where the profile creation submit button becomes disabled (darker) but nothing happens - no redirect, no error message, just a stuck state.

## Test Structure

The test suite includes 5 test cases:

1. **test_profile_creation_step1_loads** - Verifies Step 1 (URL scraper) loads correctly
2. **test_profile_creation_skip_to_manual** - Tests navigation from Step 1 to Step 2
3. **test_profile_creation_form_validation** - Tests client-side form validation
4. **test_profile_creation_complete_flow** - **Main test** - Tests complete submission with screenshot capture
5. **test_profile_creation_console_errors** - Checks for console errors during the flow

## Running the Tests

### Prerequisites

The tests require playwright to be installed. Due to a naming conflict with the local `playwright/` stub directory, you need to temporarily move it:

```bash
# Move the stub out of the way
mv playwright playwright_stub

# Install dependencies (if not already installed)
pip install playwright requests
playwright install chromium

# Run the tests
RUN_UI_SMOKE=1 PYTHONPATH=. pytest tests/e2e/test_profile_creation.py -v -s

# Restore the stub
mv playwright_stub playwright
```

### Running Individual Tests

```bash
# Run just the complete flow test (captures screenshots)
RUN_UI_SMOKE=1 PYTHONPATH=. pytest tests/e2e/test_profile_creation.py::test_profile_creation_complete_flow -v -s
```

## Screenshot Capture

The `test_profile_creation_complete_flow` test captures screenshots at key stages:

1. **01_step2_initial.png** - Initial state of Step 2
2. **02_step2_filled.png** - After filling all required fields
3. **03_before_submit.png** - Just before clicking submit
4. **04_after_submit_click.png** - Immediately after click (should show loading state)
5. **05_dashboard_success.png** OR **05_after_timeout.png** - Final state

Screenshots are saved to: `tmp/screenshots/profile_creation/`

## Debugging the "Silent Death Click"

The test monitors:
- **Console errors** - Any JavaScript errors in the browser console
- **Page errors** - Uncaught exceptions
- **Network requests** - All HTTP requests during submission
- **Button state** - Whether the button is disabled, text changes, loading indicator
- **Redirect behavior** - Whether navigation to `/dashboard` occurs

If the silent death click occurs, the test will:
1. Not redirect to the dashboard within 10 seconds
2. Capture the stuck state in a screenshot
3. Print all console errors, page errors, and network requests
4. Report the button's final state (disabled, text, loading indicator visible)

## Known Issues

### Playwright Import Conflict

The repository has a `playwright/` directory containing a stub for non-UI tests. This conflicts with the real playwright package. The test handles this by temporarily removing the repo root from `sys.path` before importing playwright.

### Database Dependency

The tests require a PostgreSQL database. You may see warnings about database connection failures, but the server should still start in dev mode with an in-memory database fallback.

## Expected Behavior vs Actual Behavior

### Expected (Normal Flow)
1. User fills out profile form
2. User clicks "Save & Continue to Dashboard"
3. Button shows loading state (disabled, spinner visible)
4. Form submits to `/onboarding` endpoint
5. Server processes and redirects to `/dashboard`
6. User sees the dashboard

### Actual (Silent Death Click)
1. User fills out profile form
2. User clicks "Save & Continue to Dashboard"
3. Button gets darker (disabled state applied)
4. **NOTHING ELSE HAPPENS** - No loading spinner, no error, no redirect
5. Button remains stuck in disabled state
6. User is confused and may try clicking again or refreshing

## Integration with CI/CD

These tests are gated by the `RUN_UI_SMOKE` environment variable. They can be added to the CI workflow under the `smoke` job that already runs UI smoke tests.

```yaml
- name: Run profile creation tests
  env:
    RUN_UI_SMOKE: '1'
  run: |
    mv playwright playwright_stub
    pytest -q tests/e2e/test_profile_creation.py --maxfail=1
    mv playwright_stub playwright
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'playwright'"

Install playwright: `pip install playwright && playwright install chromium`

### "ImportError: cannot import name 'Browser' from 'playwright.sync_api'"

The local `playwright/` stub is interfering. Move it: `mv playwright playwright_stub`

### "Connection refused at http://127.0.0.1:5001"

The test server didn't start. Check that port 5001 is available and that Flask dependencies are installed.

### Timeout waiting for auth modal

The test tries to create a user first by opening the auth modal. If the page structure has changed, update the selectors in the `create_test_user()` helper function.
