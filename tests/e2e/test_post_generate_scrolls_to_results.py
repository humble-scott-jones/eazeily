"""
Test that after generation, the page auto-scrolls to "Generated Content".

This test validates UX-GEN-FLOW-002 requirement:
"After generation, auto-scroll to 'Generated Content'"
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


def test_post_generate_scrolls_to_results():
    """
    Test that after content generation:
    1. The generated-content section becomes visible
    2. The page auto-scrolls to that section
    3. User sees the "Generated Content" header and posts
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Create a paid dev user and get session
            s = requests.Session()
            r = s.post(f'{BASE}/__dev__/create_user', json={
                'email': 'scroll-test@example.com',
                'is_paid': True
            })
            assert r.status_code == 200
            
            # Transfer cookies to browser
            cookies = s.cookies.get_dict()
            for name, val in cookies.items():
                page.context.add_cookies([{'name': name, 'value': val, 'url': BASE}])
            
            # Navigate to generate page
            page.goto(f'{BASE}/generate/social')
            page.wait_for_selector('#generate-content', timeout=5000)
            
            # Ensure we start at the top of the page
            page.evaluate('window.scrollTo(0, 0)')
            
            # The generated-content section should be hidden initially
            generated_section = page.locator('#generated-content')
            expect(generated_section).to_have_class(lambda c: 'hidden' in c)
            
            # Click generate button
            generate_btn = page.locator('#generate-content')
            generate_btn.click()
            
            # Wait for generation to complete and results to appear
            # The section should become visible
            page.wait_for_selector('#generated-content:not(.hidden)', timeout=15000)
            
            # Wait a bit for scroll animation to complete
            time.sleep(1)
            
            # Verify the generated content section is visible
            expect(generated_section).not_to_have_class(lambda c: 'hidden' in c)
            
            # Verify we can see the "Generated Content" heading
            heading = page.locator('#generated-content h2:has-text("Generated Content")')
            expect(heading).to_be_visible()
            
            # Verify posts are rendered
            posts = page.locator('.generated-post-card, .card')
            expect(posts.first).to_be_visible(timeout=5000)
            
            # Check that the generated content section is in viewport
            # This validates that auto-scroll happened
            is_in_viewport = page.evaluate('''() => {
                const el = document.getElementById('generated-content');
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                return rect.top >= 0 && rect.top <= window.innerHeight;
            }''')
            assert is_in_viewport, "Generated content section should be scrolled into viewport"
            
            browser.close()
    finally:
        stop_server(proc)
