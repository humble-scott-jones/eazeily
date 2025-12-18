"""Test that fallback banner appears when source is fallback."""

import os
import time
from playwright.sync_api import sync_playwright, expect
import subprocess
import requests
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv('PORT', '5001'))
BASE = f'http://127.0.0.1:{PORT}'

pytestmark = pytest.mark.skipif(os.getenv('RUN_UI_SMOKE') != '1', reason='UI smoke tests disabled (set RUN_UI_SMOKE=1)')


def start_server():
    """Start the Flask server for testing."""
    py = './.venv/bin/python' if (ROOT / '.venv' / 'bin' / 'python').exists() else 'python3'
    # Ensure Gemini is disabled to force fallback mode
    env = os.environ.copy()
    env.pop('GEMINI_API_KEY', None)
    env['USE_GEMINI_FOR_POSTS'] = '0'
    
    p = subprocess.Popen([py, 'app.py'], cwd=str(ROOT), env=env)
    for _ in range(30):
        try:
            r = requests.get(f'{BASE}/__dev__/ping', timeout=1)
            if r.status_code == 200:
                return p
        except Exception:
            pass
        time.sleep(0.5)
    p.kill()
    raise RuntimeError('server failed to start')


def stop_server(p):
    """Stop the Flask server."""
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def test_fallback_banner_appears_when_source_fallback():
    """Test that banner appears when API returns source=fallback."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Create a user via dev helper
            requests.post(f'{BASE}/__dev__/create_user', json={'email': 'banner-test@example.com', 'is_paid': True})
            
            # Navigate to generate page
            page.goto(f'{BASE}/generate/social')
            page.wait_for_load_state('networkidle')
            
            # Intercept API response to verify it has source field
            api_response = None
            def handle_response(response):
                nonlocal api_response
                if '/api/generate' in response.url and response.status == 200:
                    try:
                        api_response = response.json()
                    except Exception:
                        pass
            
            page.on('response', handle_response)
            
            # Wait for generate button and click it
            # The page might need interaction first
            time.sleep(1)
            
            # Try to find and click generate button
            try:
                # Look for various possible generate button selectors
                generate_btn = page.locator('button:has-text("Generate")').first
                if generate_btn.is_visible(timeout=5000):
                    generate_btn.click()
                    time.sleep(2)  # Wait for generation to complete
            except Exception as e:
                print(f"Could not find generate button: {e}")
                # Try alternative approach - directly call API via JavaScript
                page.evaluate("""
                    async function testGenerate() {
                        const res = await fetch('/api/generate', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                industry: 'realtor',
                                tone: 'friendly',
                                platforms: ['instagram'],
                                days: 1
                            })
                        });
                        const data = await res.json();
                        // Trigger renderPosts manually
                        if (window.renderPosts) {
                            window.renderPosts(data);
                        }
                        return data;
                    }
                    testGenerate();
                """)
                time.sleep(2)
            
            # Check if banner appears
            banner = page.locator('#fallback-banner')
            
            # Banner should be visible
            try:
                expect(banner).to_be_visible(timeout=5000)
                print("✓ Fallback banner is visible")
                
                # Verify banner content
                expect(banner).to_contain_text('AI generation temporarily unavailable')
                print("✓ Banner contains expected warning text")
                
                # Check for buttons
                retry_btn = banner.locator('#retry-with-ai')
                continue_btn = banner.locator('#continue-with-suggestions')
                dismiss_btn = banner.locator('#dismiss-fallback-banner')
                
                expect(retry_btn).to_be_visible()
                expect(continue_btn).to_be_visible()
                expect(dismiss_btn).to_be_visible()
                print("✓ All banner buttons are visible")
                
                # Test dismiss button
                dismiss_btn.click()
                time.sleep(0.5)
                expect(banner).to_be_hidden()
                print("✓ Banner can be dismissed")
                
                # Verify API response had correct fields
                if api_response:
                    assert 'source' in api_response, "API response missing source field"
                    assert 'mode' in api_response, "API response missing mode field"
                    assert api_response['source'] == 'fallback', f"Expected source=fallback, got {api_response['source']}"
                    assert api_response['mode'] == 'fallback_suggestions', f"Expected mode=fallback_suggestions, got {api_response['mode']}"
                    print(f"✓ API response has correct source={api_response['source']} and mode={api_response['mode']}")
                
            except Exception as e:
                # Take screenshot for debugging
                screenshot_path = '/tmp/fallback_banner_test.png'
                page.screenshot(path=screenshot_path)
                print(f"Screenshot saved to {screenshot_path}")
                raise e
            
            browser.close()
    finally:
        stop_server(proc)


def test_banner_hidden_when_source_openai():
    """Test that banner is hidden when source is openai (future test for when Gemini is available)."""
    # This test would be run when Gemini is actually configured
    # For now, we'll skip it since we're forcing fallback mode
    pytest.skip("Gemini not configured in test environment")


if __name__ == '__main__':
    # Run test manually
    test_fallback_banner_appears_when_source_fallback()
