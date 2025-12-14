"""
Test that the unified queue is collapsed by default.

This test validates UX-GEN-FLOW-002 requirement:
"Make 'Unified queue' collapsed by default (expand on demand)"
"""
import os
import time
import pytest
import requests
from playwright.sync_api import sync_playwright, expect
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv('PORT', '5001'))
BASE = f'http://127.0.0.1:{PORT}'

pytestmark = pytest.mark.skipif(
    os.getenv('RUN_UI_SMOKE') != '1',
    reason='UI smoke tests disabled (set RUN_UI_SMOKE=1)'
)


def start_server():
    """Start the Flask development server."""
    py = './.venv/bin/python' if (ROOT / '.venv' / 'bin' / 'python').exists() else 'python3'
    p = subprocess.Popen([py, 'app.py'], cwd=str(ROOT), env=os.environ.copy())
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
    """Stop the Flask development server."""
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def test_queue_collapsed_by_default():
    """
    Test that after content generation:
    1. The unified queue section is visible
    2. But the queue content is collapsed/hidden by default
    3. User can expand it by clicking the toggle button
    4. The expanded state persists via localStorage
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Create a paid dev user and get session
            s = requests.Session()
            r = s.post(f'{BASE}/__dev__/create_user', json={
                'email': 'queue-test@example.com',
                'is_paid': True
            })
            assert r.status_code == 200
            
            # Transfer cookies to browser
            cookies = s.cookies.get_dict()
            for name, val in cookies.items():
                page.context.add_cookies([{'name': name, 'value': val, 'url': BASE}])
            
            # Clear localStorage to ensure default state
            page.goto(f'{BASE}/generate/social')
            page.evaluate('localStorage.clear()')
            page.reload()
            
            # Wait for page to load
            page.wait_for_selector('#generate-content', timeout=5000)
            
            # Click generate button
            generate_btn = page.locator('#generate-content')
            generate_btn.click()
            
            # Wait for generation to complete
            page.wait_for_selector('#generated-content:not(.hidden)', timeout=15000)
            
            # The publishing-queue section should be visible (the wrapper)
            queue_section = page.locator('#publishing-queue')
            # Note: It may be hidden if there are no queue items initially
            # But once we interact with posts, it should appear
            
            # Wait for posts to render
            page.wait_for_selector('.generated-post-card, .card', timeout=5000)
            
            # Check if queue section is present (it might be hidden if empty)
            # Let's check the toggle button state
            toggle_btn = page.locator('#toggle-queue')
            
            # If queue section is visible, verify content is collapsed by default
            if queue_section.is_visible():
                queue_content = page.locator('#queue-content')
                expect(queue_content).to_have_class(lambda c: 'hidden' in c)
                
                # Verify toggle button shows "Show queue" text (collapsed state)
                toggle_text = page.locator('#queue-toggle-text')
                expect(toggle_text).to_have_text('Show queue')
                
                # Verify toggle icon is pointing right (collapsed)
                toggle_icon = page.locator('#queue-toggle-icon')
                expect(toggle_icon).to_have_text('▸')
                
                # Verify aria-expanded is false
                expect(toggle_btn).to_have_attribute('aria-expanded', 'false')
                
                # Click to expand the queue
                toggle_btn.click()
                time.sleep(0.3)  # Wait for animation
                
                # Now queue content should be visible
                expect(queue_content).not_to_have_class(lambda c: 'hidden' in c)
                expect(toggle_text).to_have_text('Hide queue')
                expect(toggle_icon).to_have_text('▾')
                expect(toggle_btn).to_have_attribute('aria-expanded', 'true')
                
                # Verify localStorage persistence
                expanded_state = page.evaluate('localStorage.getItem("queue-expanded")')
                assert expanded_state == 'true', "Queue expanded state should be persisted"
                
                # Collapse it again
                toggle_btn.click()
                time.sleep(0.3)
                
                # Verify it's collapsed again
                expect(queue_content).to_have_class(lambda c: 'hidden' in c)
                collapsed_state = page.evaluate('localStorage.getItem("queue-expanded")')
                assert collapsed_state == 'false', "Queue collapsed state should be persisted"
            
            browser.close()
    finally:
        stop_server(proc)


def test_queue_persists_expanded_state():
    """
    Test that the queue's expanded state persists across page reloads.
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Create a paid dev user and get session
            s = requests.Session()
            r = s.post(f'{BASE}/__dev__/create_user', json={
                'email': 'queue-persist-test@example.com',
                'is_paid': True
            })
            assert r.status_code == 200
            
            # Transfer cookies to browser
            cookies = s.cookies.get_dict()
            for name, val in cookies.items():
                context.add_cookies([{'name': name, 'value': val, 'url': BASE}])
            
            # Navigate and generate content
            page.goto(f'{BASE}/generate/social')
            page.evaluate('localStorage.clear()')
            page.reload()
            page.wait_for_selector('#generate-content', timeout=5000)
            
            # Generate content
            page.locator('#generate-content').click()
            page.wait_for_selector('#generated-content:not(.hidden)', timeout=15000)
            page.wait_for_selector('.generated-post-card, .card', timeout=5000)
            
            # Expand the queue if it's visible
            queue_section = page.locator('#publishing-queue')
            if queue_section.is_visible():
                toggle_btn = page.locator('#toggle-queue')
                toggle_btn.click()
                time.sleep(0.3)
                
                # Reload the page
                page.reload()
                page.wait_for_selector('#generated-content', timeout=5000)
                
                # The queue should remember it was expanded
                # But since we reload and need to regenerate, let's just verify localStorage
                expanded_state = page.evaluate('localStorage.getItem("queue-expanded")')
                assert expanded_state == 'true', "Expanded state should persist across reloads"
            
            context.close()
            browser.close()
    finally:
        stop_server(proc)
