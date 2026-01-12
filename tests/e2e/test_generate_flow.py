"""
E2E tests for content generation flow.

Tests:
1. Happy path: Saved profile → generate → editable/copyable outputs
2. Failure mode: Model missing/500 → shows actionable error + retry
"""

import os
import time
import pytest
from playwright.sync_api import sync_playwright
import subprocess
import requests
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv('PORT', '5001'))
BASE = f'http://127.0.0.1:{PORT}'

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_UI_SMOKE') != '1',
    reason='UI smoke tests disabled (set RUN_UI_SMOKE=1)'
)


def start_server():
    """Start the Flask server for e2e testing."""
    py = './.venv/bin/python' if (ROOT / '.venv' / 'bin' / 'python').exists() else 'python3'
    env = os.environ.copy()
    # Ensure API key is set for testing
    if 'GENAI_API_KEY' not in env and 'GOOGLE_API_KEY' not in env:
        env['GENAI_API_KEY'] = 'test-api-key-for-e2e'
    
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


@pytest.mark.e2e
def test_generate_flow_happy_path():
    """Test happy path: saved profile → generate → editable/copyable outputs."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Create user via dev helper
            requests.post(f'{BASE}/__dev__/create_user', json={
                'email': 'generate+test@example.com',
                'is_paid': True
            })
            
            # Set up profile via API
            requests.post(f'{BASE}/api/profile', json={
                'company': 'Test Co',
                'industry': 'technology',
                'tone': 'professional',
                'platforms': ['instagram', 'linkedin'],
                'brand_keywords': ['innovation', 'quality'],
                'goals': ['awareness', 'engagement'],
            })
            
            # Navigate to dashboard
            page.goto(f'{BASE}/dashboard')
            page.wait_for_load_state('networkidle')
            
            # Wait for profile to load
            page.wait_for_selector('[data-voice-company]', timeout=5000)
            
            # Verify profile loaded
            company_el = page.query_selector('[data-voice-company]')
            assert company_el is not None
            assert 'Test Co' in company_el.inner_text()
            
            # Find and click generate button
            generate_btn = page.query_selector('#generate-content, #generate-plan')
            assert generate_btn is not None, "Generate button not found"
            
            # Verify at least one platform is selected
            platform_chips = page.query_selector_all('[data-generator-platform].chip--active')
            assert len(platform_chips) > 0, "No platforms selected"
            
            # Click generate
            generate_btn.click()
            
            # Wait for loading state
            loading_div = page.query_selector('#content-loading, #generator-loading')
            if loading_div:
                # Wait for loading to disappear (max 30 seconds for generation)
                page.wait_for_function(
                    "el => el.classList.contains('hidden')",
                    loading_div,
                    timeout=30000
                )
            
            # Wait for results to appear
            results_div = page.query_selector('#generated-content, #content-results')
            assert results_div is not None, "Results container not found"
            
            # Verify results are visible
            page.wait_for_function(
                "el => !el.classList.contains('hidden')",
                results_div,
                timeout=5000
            )
            
            # Verify post cards are rendered
            post_cards = page.query_selector_all('.card, .post-card, [data-post-card]')
            assert len(post_cards) > 0, "No posts rendered"
            
            # Verify first post has editable textarea
            first_card = post_cards[0]
            textarea = first_card.query_selector('textarea.post-editor, textarea[id*="editor"]')
            assert textarea is not None, "No editable textarea found"
            assert len(textarea.input_value()) > 0, "Caption is empty"
            
            # Verify copy button exists and is clickable
            copy_btn = first_card.query_selector('button[data-copy-target], button:has-text("Copy")')
            assert copy_btn is not None, "Copy button not found"
            
            # Click copy button
            copy_btn.click()
            time.sleep(0.5)
            
            # Verify copy feedback appears
            copy_stamp = first_card.query_selector('.copy-timestamp, [id*="stamp"]')
            if copy_stamp:
                assert 'Copied' in copy_stamp.inner_text() or len(copy_stamp.inner_text()) > 0
            
            browser.close()
    finally:
        stop_server(proc)


@pytest.mark.e2e
def test_generate_flow_missing_provider_error():
    """Test failure mode: missing model/provider shows actionable error."""
    # Start server without API key
    py = './.venv/bin/python' if (ROOT / '.venv' / 'bin' / 'python').exists() else 'python3'
    env = os.environ.copy()
    # Remove API keys
    env.pop('GENAI_API_KEY', None)
    env.pop('GOOGLE_API_KEY', None)
    
    proc = subprocess.Popen([py, 'app.py'], cwd=str(ROOT), env=env)
    
    # Wait for server to start
    for _ in range(30):
        try:
            r = requests.get(f'{BASE}/__dev__/ping', timeout=1)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Create user
            requests.post(f'{BASE}/__dev__/create_user', json={
                'email': 'error+test@example.com',
                'is_paid': True
            })
            
            # Navigate to dashboard
            page.goto(f'{BASE}/dashboard')
            page.wait_for_load_state('networkidle')
            
            # Try to generate
            generate_btn = page.query_selector('#generate-content, #generate-plan')
            if generate_btn:
                generate_btn.click()
                
                # Wait a bit for error to appear
                time.sleep(2)
                
                # Look for error message
                status_el = page.query_selector('#generator-status, [data-status]')
                if status_el:
                    error_text = status_el.inner_text().lower()
                    # Should show clear error about missing service
                    assert 'ai service' in error_text or 'not configured' in error_text or 'api key' in error_text
                
                # Verify generate button is visible again (not stuck in loading)
                assert generate_btn.is_visible(), "Generate button should be visible after error"
            
            browser.close()
    finally:
        stop_server(proc)


@pytest.mark.e2e
def test_generate_flow_retry_after_error():
    """Test that user can retry generation after an error."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Create user
            requests.post(f'{BASE}/__dev__/create_user', json={
                'email': 'retry+test@example.com',
                'is_paid': True
            })
            
            # Set up profile
            requests.post(f'{BASE}/api/profile', json={
                'company': 'Retry Test Co',
                'industry': 'technology',
                'platforms': ['instagram'],
            })
            
            # Navigate to dashboard
            page.goto(f'{BASE}/dashboard')
            page.wait_for_load_state('networkidle')
            
            # First generation attempt
            generate_btn = page.query_selector('#generate-content, #generate-plan')
            if generate_btn:
                generate_btn.click()
                
                # Wait for completion (success or error)
                time.sleep(5)
                
                # Verify button is clickable again
                assert generate_btn.is_visible(), "Generate button not visible"
                assert not generate_btn.is_disabled(), "Generate button should not be disabled"
                
                # Try again (retry)
                generate_btn.click()
                time.sleep(5)
                
                # Should either succeed or show error, but not be stuck
                assert generate_btn.is_visible(), "Generate button not visible after retry"
            
            browser.close()
    finally:
        stop_server(proc)


@pytest.mark.e2e  
def test_model_ready_health_check():
    """Test that /api/model-ready endpoint works correctly."""
    proc = start_server()
    try:
        # Test when API key is present
        response = requests.get(f'{BASE}/api/model-ready')
        assert response.status_code in [200, 503]
        
        data = response.json()
        assert 'ok' in data
        assert 'ready' in data
        
        if response.status_code == 200:
            assert data['ok'] is True
            assert data['ready'] is True
            assert 'provider' in data
        else:
            assert data['ok'] is False
            assert data['ready'] is False
            assert 'error' in data
    finally:
        stop_server(proc)
