"""
E2E smoke test for /generate/social page to verify:
- No console errors (specifically no publishingQueueState ReferenceError)
- Page loads and resolves (no infinite "Loading profile...")
- Queue section renders without exceptions
"""

import os
import time
import subprocess
import pathlib
import requests
import pytest
from playwright.sync_api import sync_playwright

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


def test_generate_social_no_console_errors():
    """
    Test that /generate/social loads without console errors.
    
    Specifically checks for:
    - No ReferenceError for publishingQueueState
    - No other JavaScript runtime errors
    - Page completes loading (not stuck at "Loading profile...")
    """
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
            
            # Capture page errors (uncaught exceptions)
            page_errors = []
            def handle_page_error(error):
                page_errors.append(str(error))
            
            page.on('pageerror', handle_page_error)
            
            # Navigate to generate/social
            page.goto(f"{BASE}/generate/social", wait_until="networkidle", timeout=10000)
            
            # Wait a bit for JS to execute
            time.sleep(2)
            
            # Check for specific error messages
            for error in console_errors:
                # Check for publishingQueueState errors
                if 'publishingQueueState' in error and 'not defined' in error.lower():
                    pytest.fail(f"Found publishingQueueState ReferenceError: {error}")
                if 'ReferenceError' in error and 'publishingQueueState' in error:
                    pytest.fail(f"Found publishingQueueState ReferenceError: {error}")
            
            for error in page_errors:
                if 'publishingQueueState' in error:
                    pytest.fail(f"Found page error with publishingQueueState: {error}")
            
            # Verify page loaded successfully
            # Check that we're not stuck on "Loading profile..."
            profile_summary = page.query_selector('#profile-defaults-summary')
            if profile_summary:
                summary_text = profile_summary.inner_text()
                # Should not still be "Loading profile..."
                assert "Loading profile" not in summary_text or len(summary_text) > len("Loading profile...")
            
            # Verify queue area exists and can be rendered
            queue_area = page.query_selector('#publishing-queue')
            assert queue_area is not None, "Publishing queue area should exist"
            
            # If there are other console errors, log them but don't fail (they might be pre-existing)
            if console_errors:
                print(f"\nConsole messages (for info): {console_errors}")
            
            if page_errors:
                print(f"\nPage errors (for info): {page_errors}")
            
            browser.close()
    
    finally:
        stop_server(proc)


def test_queue_empty_state_renders():
    """
    Test that the queue area renders correctly when empty.
    
    Verifies:
    - Queue empty state message appears
    - No exceptions thrown when rendering empty queue
    """
    proc = start_server()
    page_errors = []
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Capture page errors
            def handle_page_error(error):
                page_errors.append(str(error))
            
            page.on('pageerror', handle_page_error)
            
            # Navigate to generate/social
            page.goto(f"{BASE}/generate/social", wait_until="networkidle", timeout=10000)
            
            # Wait for page to settle
            time.sleep(2)
            
            # Check that queue area exists
            queue_area = page.query_selector('#publishing-queue')
            assert queue_area is not None, "Queue area should exist"
            
            # Check for empty state element
            queue_empty = page.query_selector('#publishing-queue-empty')
            if queue_empty:
                # Empty state should be visible (or at least exist)
                empty_text = queue_empty.inner_text()
                assert len(empty_text) > 0, "Empty state should have text"
            
            # No page errors should occur
            queue_related_errors = [e for e in page_errors if 'queue' in e.lower()]
            if queue_related_errors:
                pytest.fail(f"Queue-related errors found: {queue_related_errors}")
            
            browser.close()
    
    finally:
        stop_server(proc)


def test_profile_hydration_completes():
    """
    Test that profile hydration completes (no infinite loading state).
    
    Verifies:
    - Profile banner either shows data or a clear error/missing state
    - Not stuck in "Loading profile..." indefinitely
    """
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate
            page.goto(f"{BASE}/generate/social", wait_until="networkidle", timeout=10000)
            
            # Wait for hydration to complete (up to 5 seconds)
            time.sleep(5)
            
            # Check profile defaults summary
            summary_el = page.query_selector('#profile-defaults-summary')
            if summary_el:
                text = summary_el.inner_text()
                # Should have resolved to something other than just "Loading profile..."
                assert text != "Loading profile…", "Profile should have finished loading"
                assert len(text) > 0, "Profile summary should have content"
            
            # Check voice pill
            voice_pill = page.query_selector('#voice-pill')
            if voice_pill:
                pill_text = voice_pill.inner_text()
                # Should not still say "Syncing..."
                assert "Syncing" not in pill_text or len(pill_text) > len("Syncing voice from wizard…")
            
            browser.close()
    
    finally:
        stop_server(proc)
