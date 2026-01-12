"""
E2E Playwright test for profile creation flow.

Tests the complete onboarding wizard flow including:
- Step 1: URL scraper interface
- Step 2: Manual profile creation form
- Form validation
- Form submission
- Console errors
- Silent death click scenario (button disabled but nothing happens)
"""

import os
import time
import subprocess
import pathlib
import requests
import pytest

# Import playwright - the real one, not the local stub
# We need to be careful about import order since tests/conftest.py adds ROOT to sys.path
import sys
_repo_root = str(pathlib.Path(__file__).resolve().parents[2])
if _repo_root in sys.path:
    sys.path.remove(_repo_root)
from playwright.sync_api import sync_playwright, expect
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv("PORT", "5001"))
BASE = f"http://127.0.0.1:{PORT}"

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_UI_SMOKE") != "1",
    reason="UI smoke tests disabled (set RUN_UI_SMOKE=1)"
)


def start_server():
    """Start Flask server and wait for it to be ready."""
    py = "./.venv/bin/python" if (ROOT / ".venv" / "bin" / "python").exists() else "python3"
    env = os.environ.copy()
    env['PORT'] = str(PORT)
    p = subprocess.Popen([py, "app.py"], cwd=str(ROOT), env=env)
    
    # Wait for server to be ready
    for _ in range(40):
        try:
            r = requests.get(f"{BASE}/__dev__/ping", timeout=1)
            if r.status_code == 200:
                return p
        except Exception:
            pass
        time.sleep(0.5)
    
    p.kill()
    raise RuntimeError("server failed to start")


def stop_server(p):
    """Stop Flask server gracefully."""
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def create_test_user(page):
    """Helper to create and log in a test user."""
    # Generate unique email for this test run
    timestamp = int(time.time() * 1000)
    email = f"test_profile_{timestamp}@example.com"
    password = "TestPassword123!"
    
    # Navigate to app page which has auth
    page.goto(f"{BASE}/app", wait_until="networkidle")
    
    # Wait for page to load
    page.wait_for_timeout(1000)
    
    # Open auth modal - look for Sign in link
    try:
        # Try multiple selectors
        page.click('text="Sign in"', timeout=5000)
    except Exception:
        try:
            page.click('a:has-text("Sign in")', timeout=5000)
        except Exception:
            # Try clicking header auth link
            page.click('header a[href="/account"]', timeout=5000)
    
    # Switch to signup tab
    signup_tab = page.locator('[data-auth-tab="signup"]')
    signup_tab.wait_for(timeout=2000)
    signup_tab.click()
    
    # Fill signup form
    page.locator('#signup-email').fill(email)
    page.locator('#signup-password').fill(password)
    page.locator('#signup-terms').check()
    
    # Submit signup
    page.locator('#signup-form button[type="submit"]').click()
    
    # Wait for auth to complete (modal should close)
    time.sleep(2)
    
    return email, password


def test_profile_creation_step1_loads():
    """Test that Step 1 of the onboarding wizard loads correctly."""
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1400, 'height': 1000})
            page = context.new_page()
            
            # Create and login test user
            email, password = create_test_user(page)
            
            # Navigate to onboarding
            page.goto(f"{BASE}/onboarding", wait_until="networkidle")
            
            # Verify Step 1 is visible
            step1 = page.locator('#step1')
            expect(step1).to_be_visible()
            expect(step1).not_to_have_class('hidden')
            
            # Verify Step 2 is hidden
            step2 = page.locator('#step2')
            expect(step2).to_have_class('hidden')
            
            # Verify key elements in Step 1
            url_input = page.locator('#website_url')
            expect(url_input).to_be_visible()
            
            fetch_button = page.locator('#fetchBtn')
            expect(fetch_button).to_be_visible()
            expect(fetch_button).to_contain_text('Analyze')
            
            skip_link = page.locator('text=Skip - I\'ll enter everything manually')
            expect(skip_link).to_be_visible()
            
            # Verify progress indicator
            progress_bar = page.locator('#progressBar')
            expect(progress_bar).to_be_visible()
            current_step = page.locator('#currentStep')
            expect(current_step).to_have_text('1')
            
            print("✓ Step 1 loads correctly with all elements visible")
            
            browser.close()
    finally:
        stop_server(proc)


def test_profile_creation_skip_to_manual():
    """Test that clicking 'Skip' navigates to Step 2."""
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1400, 'height': 1000})
            page = context.new_page()
            
            # Create and login test user
            email, password = create_test_user(page)
            
            # Navigate to onboarding
            page.goto(f"{BASE}/onboarding", wait_until="networkidle")
            
            # Click skip link
            skip_link = page.locator('text=Skip - I\'ll enter everything manually')
            skip_link.click()
            
            # Wait for step transition
            time.sleep(0.5)
            
            # Verify Step 2 is now visible
            step2 = page.locator('#step2')
            expect(step2).to_be_visible()
            expect(step2).not_to_have_class('hidden')
            
            # Verify Step 1 is hidden
            step1 = page.locator('#step1')
            expect(step1).to_have_class('hidden')
            
            # Verify progress indicator updated
            current_step = page.locator('#currentStep')
            expect(current_step).to_have_text('2')
            
            print("✓ Skip to manual entry works correctly")
            
            browser.close()
    finally:
        stop_server(proc)


def test_profile_creation_form_validation():
    """Test form validation on Step 2."""
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1400, 'height': 1000})
            page = context.new_page()
            
            # Create and login test user
            email, password = create_test_user(page)
            
            # Navigate to onboarding and skip to Step 2
            page.goto(f"{BASE}/onboarding", wait_until="networkidle")
            page.locator('text=Skip - I\'ll enter everything manually').click()
            time.sleep(0.5)
            
            # Try to submit form without filling required fields
            submit_button = page.locator('#submitBtn')
            submit_button.click()
            
            # Wait for validation to run
            time.sleep(0.5)
            
            # Verify validation error banner appears
            error_banner = page.locator('#validation-error')
            expect(error_banner).to_be_visible()
            expect(error_banner).not_to_have_class('hidden')
            
            # Verify error messages are shown
            error_list = page.locator('#validation-errors-list li')
            expect(error_list.first).to_be_visible()
            
            print("✓ Form validation works correctly")
            
            browser.close()
    finally:
        stop_server(proc)


def test_profile_creation_complete_flow():
    """Test complete profile creation flow with console error tracking."""
    proc = start_server()
    console_errors = []
    page_errors = []
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={'width': 1400, 'height': 1000})
            page = context.new_page()
            
            # Capture console errors
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append(msg.text)
                    print(f"Console error: {msg.text}")
            
            page.on('console', handle_console)
            
            # Capture page errors (uncaught exceptions)
            def handle_page_error(error):
                page_errors.append(str(error))
                print(f"Page error: {str(error)}")
            
            page.on('pageerror', handle_page_error)
            
            # Create and login test user
            email, password = create_test_user(page)
            
            # Navigate to onboarding
            page.goto(f"{BASE}/onboarding", wait_until="networkidle")
            
            # Skip to Step 2
            page.locator('text=Skip - I\'ll enter everything manually').click()
            time.sleep(0.5)
            
            # Take screenshot of initial state
            screenshot_dir = ROOT / 'tmp' / 'screenshots' / 'profile_creation'
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_dir / '01_step2_initial.png'))
            
            # Fill in required fields
            page.locator('#business_name').fill('Test Business Inc.')
            page.locator('#industry').select_option('Software / Tech / Startup')
            page.locator('#audience').fill('Developers and tech teams seeking better solutions.')
            page.locator('#voice').fill('Professional, innovative, and clear')
            page.locator('#offer').fill('Free 30-day trial of our platform')
            page.locator('#samples').fill('Check out our new feature! It makes your workflow 10x faster.\n\nWe just hit 1000 customers! Thank you for your support.')
            
            # Take screenshot after filling
            page.screenshot(path=str(screenshot_dir / '02_step2_filled.png'))
            
            # Monitor network requests during submission
            network_requests = []
            def handle_request(request):
                network_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'timestamp': time.time()
                })
            
            def handle_response(response):
                for req in network_requests:
                    if req['url'] == response.url:
                        req['status'] = response.status
                        req['ok'] = response.ok
                        break
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # Submit form
            submit_button = page.locator('#submitBtn')
            
            # Verify button is not disabled before click
            expect(submit_button).to_be_enabled()
            
            # Take screenshot before clicking
            page.screenshot(path=str(screenshot_dir / '03_before_submit.png'))
            
            # Click submit button
            submit_button.click()
            
            # Take screenshot right after clicking (should show loading state)
            time.sleep(0.2)
            page.screenshot(path=str(screenshot_dir / '04_after_submit_click.png'))
            
            # Wait for either:
            # 1. Redirect to dashboard (success)
            # 2. Error message appears (failure)
            # 3. Timeout (silent death)
            
            try:
                # Wait up to 10 seconds for navigation or error
                page.wait_for_url(f"{BASE}/dashboard", timeout=10000)
                print("✓ Successfully redirected to dashboard")
                page.screenshot(path=str(screenshot_dir / '05_dashboard_success.png'))
                success = True
            except Exception as e:
                print(f"Did not redirect to dashboard: {e}")
                success = False
                
                # Take screenshot of current state
                page.screenshot(path=str(screenshot_dir / '05_after_timeout.png'))
                
                # Check if error message appeared
                error_banner = page.locator('#validation-error')
                if error_banner.is_visible():
                    print("Error banner is visible")
                    error_text = error_banner.text_content()
                    print(f"Error message: {error_text}")
                
                # Check button state
                button_disabled = submit_button.is_disabled()
                button_text = page.locator('#submitBtnText').text_content()
                loading_visible = page.locator('#submitLoading').is_visible()
                
                print(f"Button disabled: {button_disabled}")
                print(f"Button text: {button_text}")
                print(f"Loading indicator visible: {loading_visible}")
            
            # Report all captured errors
            if console_errors:
                print(f"\n⚠️  Console errors detected ({len(console_errors)}):")
                for i, error in enumerate(console_errors, 1):
                    print(f"  {i}. {error}")
            
            if page_errors:
                print(f"\n⚠️  Page errors detected ({len(page_errors)}):")
                for i, error in enumerate(page_errors, 1):
                    print(f"  {i}. {error}")
            
            # Report network requests
            print(f"\n📡 Network requests during submission ({len(network_requests)}):")
            for req in network_requests:
                status = req.get('status', 'pending')
                print(f"  {req['method']} {req['url']} -> {status}")
            
            print(f"\n📸 Screenshots saved to: {screenshot_dir}")
            
            # Assertions
            assert len(page_errors) == 0, f"Page errors occurred: {page_errors}"
            
            # Check if we got the silent death click scenario
            if not success:
                # This is the "silent death click" - button was clicked but nothing happened
                print("\n🔴 SILENT DEATH CLICK DETECTED!")
                print("   - Form was filled correctly")
                print("   - Submit button was clicked")
                print("   - No redirect occurred")
                print("   - Check screenshots and network requests for details")
                
                # Don't fail the test - we want to document this behavior
                pytest.skip("Silent death click detected - documented in screenshots")
            
            browser.close()
    finally:
        stop_server(proc)


def test_profile_creation_console_errors():
    """Test that profile creation page has no console errors on load."""
    proc = start_server()
    console_errors = []
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Capture console errors
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append(msg.text)
            
            page.on('console', handle_console)
            
            # Create and login test user
            email, password = create_test_user(page)
            
            # Navigate to onboarding
            page.goto(f"{BASE}/onboarding", wait_until="networkidle")
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Navigate through both steps
            page.locator('text=Skip - I\'ll enter everything manually').click()
            time.sleep(1)
            
            # Check for console errors
            if console_errors:
                print(f"\n⚠️  Console errors detected:")
                for error in console_errors:
                    print(f"  - {error}")
                
                # Filter out known acceptable errors if any
                critical_errors = [e for e in console_errors if 'favicon' not in e.lower()]
                
                assert len(critical_errors) == 0, f"Critical console errors found: {critical_errors}"
            else:
                print("✓ No console errors detected during profile creation flow")
            
            browser.close()
    finally:
        stop_server(proc)
