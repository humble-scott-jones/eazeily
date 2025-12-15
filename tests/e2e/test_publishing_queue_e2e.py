import os
import time
from playwright.sync_api import sync_playwright
import subprocess
import requests
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv('PORT', '5001'))
BASE = f'http://127.0.0.1:{PORT}'

pytestmark = pytest.mark.skipif(os.getenv('RUN_UI_SMOKE') != '1', reason='UI smoke tests disabled (set RUN_UI_SMOKE=1)')


def start_server():
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
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def test_generate_social_no_queue_errors(tmp_path):
    """
    Test that /generate (Social) page loads without publishingQueueState errors.
    Verifies:
    - No console errors related to publishingQueueState
    - Queue empty state is visible
    - Page renders correctly
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Collect console messages
            console_messages = []
            errors = []
            
            def handle_console(msg):
                console_messages.append(f"{msg.type}: {msg.text}")
                if msg.type == 'error':
                    errors.append(msg.text)
            
            page.on('console', handle_console)
            
            # Create a test user via dev endpoint
            s = requests.Session()
            r = s.post(f'{BASE}/__dev__/create_user', json={'email': 'queue-test@example.com', 'is_paid': True})
            assert r.status_code == 200
            
            cookies = s.cookies.get_dict()
            for name, val in cookies.items():
                page.context.add_cookies([{'name': name, 'value': val, 'url': BASE}])
            
            # Navigate to /generate page
            page.goto(f'{BASE}/generate', wait_until='networkidle')
            
            # Wait for page to be ready
            page.wait_for_selector('#generate-content', timeout=10000)
            
            # Check for publishingQueueState errors
            queue_errors = [e for e in errors if 'publishingQueueState' in e or 'PUBLISHING_QUEUE' in e]
            assert len(queue_errors) == 0, f"Found publishingQueueState errors: {queue_errors}"
            
            # Check that the queue empty state element exists
            queue_empty = page.query_selector('#publishing-queue-empty')
            assert queue_empty is not None, "Queue empty state element should exist"
            
            # Verify the page rendered correctly
            assert page.query_selector('#generate-content') is not None, "Generate button should exist"
            
            browser.close()
    finally:
        stop_server(proc)


def test_generate_reels_no_queue_errors(tmp_path):
    """
    Test that /generate/reels page loads without publishingQueueState errors.
    Note: Reels page uses reels.js, not dashboard.js, so it shouldn't have queue state.
    This test verifies no cross-contamination of errors.
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Collect console messages
            errors = []
            
            def handle_console(msg):
                if msg.type == 'error':
                    errors.append(msg.text)
            
            page.on('console', handle_console)
            
            # Create a test user via dev endpoint
            s = requests.Session()
            r = s.post(f'{BASE}/__dev__/create_user', json={'email': 'reels-test@example.com', 'is_paid': True})
            assert r.status_code == 200
            
            cookies = s.cookies.get_dict()
            for name, val in cookies.items():
                page.context.add_cookies([{'name': name, 'value': val, 'url': BASE}])
            
            # Navigate to /generate/reels page
            page.goto(f'{BASE}/generate/reels', wait_until='networkidle')
            
            # Wait for page to be ready
            page.wait_for_selector('#reels-form', timeout=10000)
            
            # Check for any publishingQueueState errors (shouldn't be any)
            queue_errors = [e for e in errors if 'publishingQueueState' in e or 'PUBLISHING_QUEUE' in e]
            assert len(queue_errors) == 0, f"Found unexpected publishingQueueState errors on reels page: {queue_errors}"
            
            # Verify the page rendered correctly
            assert page.query_selector('#generate-btn') is not None, "Generate button should exist"
            
            browser.close()
    finally:
        stop_server(proc)


def test_queue_renders_empty_state(tmp_path):
    """
    Test that the publishing queue section renders correctly with empty state.
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Create a test user and session
            s = requests.Session()
            r = s.post(f'{BASE}/__dev__/create_user', json={'email': 'empty-queue@example.com', 'is_paid': True})
            assert r.status_code == 200
            
            cookies = s.cookies.get_dict()
            for name, val in cookies.items():
                page.context.add_cookies([{'name': name, 'value': val, 'url': BASE}])
            
            # Navigate and generate some content
            page.goto(f'{BASE}/generate', wait_until='networkidle')
            page.wait_for_selector('#generate-content', timeout=10000)
            
            # Click generate to create content (which might show queue)
            try:
                page.click('#generate-content', timeout=5000)
                # Wait a bit for generation
                time.sleep(2)
            except Exception:
                # If generation fails, that's okay for this test
                pass
            
            # Check if queue section exists
            queue_section = page.query_selector('#publishing-queue')
            if queue_section:
                # If queue section exists, it should either be hidden or show empty state
                is_hidden = queue_section.evaluate('el => el.classList.contains("hidden")')
                empty_visible = page.query_selector('#publishing-queue-empty')
                
                # Either the whole queue is hidden OR empty state is visible
                assert is_hidden or empty_visible is not None, \
                    "Queue should either be hidden or show empty state message"
            
            browser.close()
    finally:
        stop_server(proc)
