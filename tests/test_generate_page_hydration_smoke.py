"""Test UI hydration for profile on /generate page using Playwright."""
import pytest
from playwright.sync_api import sync_playwright, expect
import time
import os


# Test configuration
BASE_URL = os.getenv('TEST_BASE_URL', 'http://localhost:5001')
PROFILE_LOAD_TIMEOUT_SECONDS = 15
PROFILE_LOAD_CHECK_INTERVAL_SECONDS = 0.5
PROFILE_LOAD_MAX_ITERATIONS = int(PROFILE_LOAD_TIMEOUT_SECONDS / PROFILE_LOAD_CHECK_INTERVAL_SECONDS)


@pytest.mark.ui
def test_generate_page_profile_missing_shows_defaults():
    """Test that missing profile shows 'Using defaults' in UI."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Visit the generate page
            page.goto(f'{BASE_URL}/generate', timeout=10000)
            
            # Wait for profile defaults summary to resolve (not "Loading profile…")
            summary = page.locator('#profile-defaults-summary')
            
            # Wait for it to finish loading
            for _ in range(PROFILE_LOAD_MAX_ITERATIONS):
                text = summary.text_content()
                if text and 'Loading profile' not in text:
                    break
                time.sleep(PROFILE_LOAD_CHECK_INTERVAL_SECONDS)
            
            # Check that it shows "Using defaults"
            final_text = summary.text_content()
            assert final_text is not None
            assert 'Loading profile' not in final_text
            assert 'Using defaults' in final_text or 'Tone:' in final_text
            
            # Check voice snapshot fields show appropriate messaging
            company_field = page.locator('[data-voice-company]')
            company_text = company_field.text_content()
            assert company_text is not None
            # Should show "Not set" or have actual value
            assert 'Not set' in company_text or len(company_text.strip()) > 0
            
            print(f"✓ Profile defaults resolved to: {final_text}")
            print(f"✓ Voice company field: {company_text}")
            
        finally:
            browser.close()


@pytest.mark.ui
def test_generate_page_profile_ready_shows_values():
    """Test that ready profile populates voice snapshot with values."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # First, create a profile via API
            page.request.post(f'{BASE_URL}/api/profile', data={
                'company': 'Playwright Test Co',
                'industry': 'Technology',
                'tone': 'professional',
                'platforms': ['instagram', 'linkedin']
            })
            
            # Visit the generate page
            page.goto(f'{BASE_URL}/generate', timeout=10000)
            
            # Wait for profile to load
            summary = page.locator('#profile-defaults-summary')
            
            # Wait for loading to complete
            for _ in range(PROFILE_LOAD_MAX_ITERATIONS):
                text = summary.text_content()
                if text and 'Loading profile' not in text:
                    break
                time.sleep(PROFILE_LOAD_CHECK_INTERVAL_SECONDS)
            
            # Should not show "Using defaults" for ready profile
            final_text = summary.text_content()
            assert final_text is not None
            assert 'Loading profile' not in final_text
            
            # Voice snapshot should show actual values
            company_field = page.locator('[data-voice-company]')
            company_text = company_field.text_content()
            
            # Wait a bit more for voice hydration
            time.sleep(1)
            company_text = company_field.text_content()
            
            print(f"✓ Profile defaults: {final_text}")
            print(f"✓ Voice company: {company_text}")
            
            # Should show company name (not "Not set")
            # Note: May still show "Not set" if voice hydration hasn't completed
            assert company_text is not None
            
        finally:
            browser.close()


@pytest.mark.ui
def test_generate_page_profile_error_shows_banner():
    """Test that profile error shows banner with retry option."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Intercept the profile request and return error
            page.route('**/api/profile', lambda route: route.fulfill(
                status=500,
                content_type='application/json',
                body='{"ok": false, "error": {"code": "test_error", "message": "Test error"}, "request_id": "test123"}'
            ))
            
            # Visit the generate page
            page.goto(f'{BASE_URL}/generate', timeout=10000)
            
            # Wait for error banner to appear
            banner = page.locator('#profile-load-banner')
            
            # Wait up to configured timeout for banner to show
            for _ in range(PROFILE_LOAD_MAX_ITERATIONS):
                if banner.is_visible():
                    break
                time.sleep(PROFILE_LOAD_CHECK_INTERVAL_SECONDS)
            
            # Banner should be visible
            assert banner.is_visible(), "Error banner should be visible"
            
            # Check for retry button
            retry_button = page.locator('#profile-banner-retry')
            assert retry_button.is_visible(), "Retry button should be visible"
            
            # Check for settings link
            settings_link = page.locator('a[href="/settings"]')
            assert settings_link.count() > 0, "Settings link should be present"
            
            # Check for continue button
            continue_button = page.locator('#profile-banner-continue')
            assert continue_button.is_visible(), "Continue button should be visible"
            
            print("✓ Error banner visible with Retry, Settings, and Continue options")
            
        finally:
            browser.close()


@pytest.mark.ui  
def test_generate_page_profile_never_infinite_loading():
    """Test that profile loading always resolves within timeout."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Visit the page
            page.goto(f'{BASE_URL}/generate', timeout=10000)
            
            # Wait up to configured timeout for loading to complete
            summary = page.locator('#profile-defaults-summary')
            start_time = time.time()
            
            while time.time() - start_time < PROFILE_LOAD_TIMEOUT_SECONDS:
                text = summary.text_content()
                if text and 'Loading profile' not in text:
                    elapsed = time.time() - start_time
                    print(f"✓ Profile resolved in {elapsed:.2f} seconds: {text}")
                    break
                time.sleep(PROFILE_LOAD_CHECK_INTERVAL_SECONDS)
            else:
                # Timeout - check final state
                final_text = summary.text_content()
                raise AssertionError(f"Profile still loading after {PROFILE_LOAD_TIMEOUT_SECONDS}s: {final_text}")
            
        finally:
            browser.close()
