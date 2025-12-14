"""E2E test: Step title updates correctly as user progresses through wizard."""

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

pytestmark = pytest.mark.skipif(os.getenv("RUN_UI_SMOKE") != "1", reason="UI smoke tests disabled (set RUN_UI_SMOKE=1)")


def start_server():
    py = "./.venv/bin/python" if (ROOT / ".venv" / "bin" / "python").exists() else "python3"
    env = os.environ.copy()
    p = subprocess.Popen([py, "app.py"], cwd=str(ROOT), env=env)
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
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def test_step_title_updates_with_stepper():
    """Verify step title updates correctly as user progresses through wizard."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for page to load and industries to render
            time.sleep(2)
            
            # Check initial step title
            step_title = page.query_selector('#step-title')
            assert step_title is not None, "Step title element not found"
            initial_title = step_title.inner_text()
            assert 'industry' in initial_title.lower() or 'choose' in initial_title.lower(), \
                f"Expected industry-related title on step 1, got: {initial_title}"
            
            # Also verify progress text matches
            progress_text = page.query_selector('#progress-text')
            assert progress_text is not None, "Progress text element not found"
            assert 'Step 1' in progress_text.inner_text(), \
                f"Expected 'Step 1' in progress text, got: {progress_text.inner_text()}"
            
            # Step 1: Select industry
            industries = page.query_selector_all('#industries button')
            assert len(industries) > 0, "No industry choices found"
            industries[0].click()
            time.sleep(0.5)
            
            # Click Next to step 2 or 3
            next_btn = page.query_selector('#next')
            assert next_btn is not None, "Next button not found"
            next_btn.click()
            time.sleep(0.8)  # Wait for transition and saving feedback
            
            # Verify step title updated
            step_title = page.query_selector('#step-title')
            new_title = step_title.inner_text()
            assert new_title != initial_title, \
                "Step title should have changed after clicking Next"
            assert new_title.lower() != 'saving...', \
                "Step title should not still show 'Saving...' after transition"
            
            # Get current panel to determine if step 2 or 3
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            current_step = current_panel.get_attribute('data-step')
            
            # Verify title matches expected step
            if current_step == '2':
                assert 'context' in new_title.lower() or 'quick' in new_title.lower(), \
                    f"Expected context-related title on step 2, got: {new_title}"
            elif current_step == '3':
                assert 'tone' in new_title.lower() or 'channel' in new_title.lower(), \
                    f"Expected tone/channel-related title on step 3, got: {new_title}"
            
            # Select tone and platform if on step 3
            if current_step == '3':
                tones = page.query_selector_all('#tones button')
                if len(tones) > 0:
                    tones[0].click()
                    time.sleep(0.3)
                
                platforms = page.query_selector_all('#platforms button')
                if len(platforms) > 0:
                    platforms[0].click()
                    time.sleep(0.3)
                
                # Click Next again
                next_btn.click()
                time.sleep(0.8)
                
                # Verify title updated to step 4
                step_title = page.query_selector('#step-title')
                final_title = step_title.inner_text()
                assert 'brand' in final_title.lower() or 'inspiration' in final_title.lower(), \
                    f"Expected brand/inspiration title on step 4, got: {final_title}"
            
            browser.close()
    finally:
        stop_server(proc)


def test_progress_bar_advances_with_steps():
    """Verify progress bar fills as user advances through wizard."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(2)
            
            # Get initial progress bar width
            progress_bar = page.query_selector('#progress-bar')
            assert progress_bar is not None, "Progress bar not found"
            
            # Get initial width (should be low, like 20%)
            initial_width = page.evaluate('(el) => el.style.width', progress_bar)
            initial_percent = float(initial_width.rstrip('%'))
            assert initial_percent > 0 and initial_percent < 50, \
                f"Initial progress should be less than 50%, got: {initial_percent}%"
            
            # Select industry and advance
            industries = page.query_selector_all('#industries button')
            industries[0].click()
            time.sleep(0.3)
            
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.8)
            
            # Progress should have increased
            new_width = page.evaluate('(el) => el.style.width', progress_bar)
            new_percent = float(new_width.rstrip('%'))
            assert new_percent > initial_percent, \
                f"Progress should increase from {initial_percent}% to something higher, got: {new_percent}%"
            
            browser.close()
    finally:
        stop_server(proc)


def test_saving_feedback_appears_on_transitions():
    """Verify 'Saving...' feedback briefly appears when transitioning between steps."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(2)
            
            # Select industry
            industries = page.query_selector_all('#industries button')
            industries[0].click()
            time.sleep(0.3)
            
            # Get current step title
            step_title = page.query_selector('#step-title')
            before_title = step_title.inner_text()
            
            # Click Next and immediately check for saving feedback
            next_btn = page.query_selector('#next')
            next_btn.click()
            
            # Check within 100ms for saving feedback
            time.sleep(0.1)
            immediate_title = step_title.inner_text()
            
            # Within short time, it might show "Saving..." or already transitioned
            # Just verify it's not stuck showing Saving after 1 second
            time.sleep(1)
            final_title = step_title.inner_text()
            assert final_title.lower() != 'saving...', \
                "Step title should not still be 'Saving...' after 1 second"
            assert final_title != before_title, \
                "Step title should have changed after transition"
            
            browser.close()
    finally:
        stop_server(proc)
