#!/usr/bin/env python3
"""
Standalone script to reproduce the profile creation "silent death click" issue.

This script:
1. Starts the Flask server
2. Creates a test user
3. Fills out the profile creation form
4. Clicks submit and monitors what happens
5. Takes screenshots at each step
6. Reports any issues found

Usage:
    # Move playwright stub temporarily
    mv playwright playwright_stub
    
    # Install dependencies
    pip install playwright requests
    playwright install chromium
    
    # Run script
    python3 scripts/test_profile_creation_flow.py
    
    # Restore stub
    mv playwright_stub playwright
"""

import os
import sys
import time
import subprocess
import pathlib
import signal

# Get repo root
ROOT = pathlib.Path(__file__).resolve().parents[1]

# Import playwright - remove repo root from path first to avoid stub
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
from playwright.sync_api import sync_playwright
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests

PORT = int(os.getenv('PORT', '5001'))
BASE = f'http://127.0.0.1:{PORT}'


def start_server():
    """Start Flask server and wait for it to be ready."""
    print(f"🚀 Starting Flask server on port {PORT}...")
    py = str(ROOT / ".venv" / "bin" / "python") if (ROOT / ".venv" / "bin" / "python").exists() else "python3"
    env = os.environ.copy()
    env['PORT'] = str(PORT)
    env['FLASK_ENV'] = 'development'
    
    p = subprocess.Popen([py, "app.py"], cwd=str(ROOT), env=env, 
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    for i in range(40):
        try:
            r = requests.get(f"{BASE}/__dev__/ping", timeout=1)
            if r.status_code == 200:
                print(f"✅ Server ready after {i+1} attempts")
                return p
        except Exception:
            pass
        time.sleep(0.5)
    
    p.kill()
    raise RuntimeError("❌ Server failed to start")


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


def main():
    """Run the profile creation flow test."""
    print("\n" + "="*70)
    print("  Profile Creation Flow Test")
    print("  Testing for 'silent death click' issue")
    print("="*70 + "\n")
    
    # Start server
    proc = start_server()
    
    # Create screenshot directory
    screenshot_dir = ROOT / 'tmp' / 'screenshots' / 'profile_test'
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    print(f"📸 Screenshots will be saved to: {screenshot_dir}\n")
    
    console_errors = []
    page_errors = []
    network_requests = []
    
    try:
        with sync_playwright() as pw:
            print("🌐 Launching browser...")
            browser = pw.chromium.launch(headless=False)  # headless=False to see what happens
            context = browser.new_context(viewport={'width': 1400, 'height': 1000})
            page = context.new_page()
            
            # Capture console errors
            def handle_console(msg):
                if msg.type == 'error':
                    console_errors.append(msg.text)
                    print(f"  ⚠️  Console error: {msg.text}")
            
            page.on('console', handle_console)
            
            # Capture page errors
            def handle_page_error(error):
                page_errors.append(str(error))
                print(f"  ❌ Page error: {str(error)}")
            
            page.on('pageerror', handle_page_error)
            
            # Monitor network requests
            def handle_request(request):
                if '/onboarding' in request.url or '/api/' in request.url:
                    network_requests.append({
                        'url': request.url,
                        'method': request.method,
                        'timestamp': time.time()
                    })
            
            def handle_response(response):
                if '/onboarding' in response.url or '/api/' in response.url:
                    for req in network_requests:
                        if req['url'] == response.url:
                            req['status'] = response.status
                            req['ok'] = response.ok
                            print(f"  📡 {req['method']} {response.url} -> {response.status}")
                            break
            
            page.on('request', handle_request)
            page.on('response', handle_response)
            
            # Step 1: Create test user
            print("\n📝 Step 1: Creating test user...")
            timestamp = int(time.time() * 1000)
            email = f"test_profile_{timestamp}@example.com"
            password = "TestPassword123!"
            
            page.goto(f"{BASE}/app", wait_until="networkidle")
            page.screenshot(path=str(screenshot_dir / '01_app_page.png'))
            
            # Try to find and click sign in
            try:
                page.wait_for_selector('text="Sign in"', timeout=3000)
                page.click('text="Sign in"')
            except Exception:
                print("  ℹ️  No Sign in button found - might already be in auth state")
            
            time.sleep(1)
            page.screenshot(path=str(screenshot_dir / '02_auth_modal.png'))
            
            # Click signup tab
            try:
                page.click('[data-auth-tab="signup"]')
                time.sleep(0.5)
                
                # Fill signup form
                page.fill('#signup-email', email)
                page.fill('#signup-password', password)
                page.check('#signup-terms')
                
                page.screenshot(path=str(screenshot_dir / '03_signup_filled.png'))
                
                # Submit
                page.click('#signup-form button[type="submit"]')
                time.sleep(2)
                
                print(f"  ✅ User created: {email}")
            except Exception as e:
                print(f"  ⚠️  Signup flow issue (might be already logged in): {e}")
            
            # Step 2: Navigate to onboarding
            print("\n📝 Step 2: Navigating to onboarding wizard...")
            page.goto(f"{BASE}/onboarding", wait_until="networkidle")
            time.sleep(1)
            page.screenshot(path=str(screenshot_dir / '04_onboarding_step1.png'))
            print("  ✅ Onboarding page loaded")
            
            # Step 3: Skip to manual entry
            print("\n📝 Step 3: Skipping to manual entry (Step 2)...")
            page.click('text="Skip - I\'ll enter everything manually"')
            time.sleep(0.5)
            page.screenshot(path=str(screenshot_dir / '05_step2_empty.png'))
            print("  ✅ Navigated to Step 2")
            
            # Step 4: Fill out the form
            print("\n📝 Step 4: Filling out profile form...")
            page.fill('#business_name', 'Test Business Inc.')
            page.select_option('#industry', 'Software / Tech / Startup')
            page.fill('#audience', 'Developers and tech teams seeking innovative solutions.')
            page.fill('#voice', 'Professional, innovative, and clear')
            page.fill('#offer', 'Free 30-day trial of our platform')
            page.fill('#samples', 'Check out our new feature! It makes your workflow 10x faster.\n\nWe just hit 1000 customers! Thank you for your support.')
            
            time.sleep(0.5)
            page.screenshot(path=str(screenshot_dir / '06_step2_filled.png'))
            print("  ✅ Form filled out")
            
            # Step 5: Click submit and monitor
            print("\n📝 Step 5: Clicking submit button...")
            print("  👀 Monitoring button state and network activity...")
            
            submit_button = page.locator('#submitBtn')
            
            # Take screenshot before clicking
            page.screenshot(path=str(screenshot_dir / '07_before_submit.png'))
            
            # Click submit
            submit_button.click()
            
            # Immediately check state
            time.sleep(0.2)
            page.screenshot(path=str(screenshot_dir / '08_immediately_after_click.png'))
            
            button_disabled = submit_button.is_disabled()
            button_text = page.locator('#submitBtnText').text_content()
            loading_visible = page.locator('#submitLoading').is_visible()
            
            print(f"  📊 Button state (0.2s after click):")
            print(f"     - Disabled: {button_disabled}")
            print(f"     - Text: '{button_text}'")
            print(f"     - Loading indicator: {loading_visible}")
            
            # Wait and monitor for redirect or error
            print("\n  ⏳ Waiting for redirect or error (max 10 seconds)...")
            success = False
            
            try:
                page.wait_for_url(f"{BASE}/dashboard", timeout=10000)
                print("  ✅ SUCCESS! Redirected to dashboard")
                page.screenshot(path=str(screenshot_dir / '09_dashboard_success.png'))
                success = True
            except Exception:
                print("  ❌ Did NOT redirect to dashboard")
                page.screenshot(path=str(screenshot_dir / '09_stuck_state.png'))
                
                # Check for error message
                error_banner = page.locator('#validation-error')
                if error_banner.is_visible():
                    error_text = error_banner.text_content()
                    print(f"  📋 Error message visible: {error_text}")
                else:
                    print("  ⚠️  No error message visible")
                
                # Check final button state
                button_disabled = submit_button.is_disabled()
                button_text = page.locator('#submitBtnText').text_content()
                loading_visible = page.locator('#submitLoading').is_visible()
                
                print(f"  📊 Final button state:")
                print(f"     - Disabled: {button_disabled}")
                print(f"     - Text: '{button_text}'")
                print(f"     - Loading indicator: {loading_visible}")
                
                if button_disabled and not loading_visible and 'Saving' not in button_text:
                    print("\n  🔴 SILENT DEATH CLICK DETECTED!")
                    print("     - Button is disabled (darker)")
                    print("     - No loading indicator")
                    print("     - No error message")
                    print("     - No redirect")
                    print("     - User is stuck!")
            
            # Report summary
            print("\n" + "="*70)
            print("  SUMMARY")
            print("="*70)
            
            if success:
                print("\n✅ Profile creation SUCCEEDED")
            else:
                print("\n❌ Profile creation FAILED or STUCK")
            
            if console_errors:
                print(f"\n⚠️  Console errors: {len(console_errors)}")
                for error in console_errors[:5]:
                    print(f"   - {error}")
            else:
                print("\n✅ No console errors")
            
            if page_errors:
                print(f"\n❌ Page errors: {len(page_errors)}")
                for error in page_errors:
                    print(f"   - {error}")
            else:
                print("\n✅ No page errors")
            
            if network_requests:
                print(f"\n📡 Network requests to /onboarding or /api/:")
                for req in network_requests:
                    status = req.get('status', 'pending')
                    print(f"   {req['method']} {req['url']}")
                    print(f"      Status: {status}, OK: {req.get('ok', 'N/A')}")
            
            print(f"\n📸 All screenshots saved to:")
            print(f"   {screenshot_dir}")
            
            print("\n✨ Press Enter to close browser and stop server...")
            input()
            
            browser.close()
            
    finally:
        print("\n🛑 Stopping server...")
        stop_server(proc)
        print("✅ Done!\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
