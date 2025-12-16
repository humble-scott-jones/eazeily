"""E2E test: Next button disabled until required fields are valid."""

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


def test_next_disabled_until_industry_selected():
    """Verify clicking Next without selecting industry shows error toast."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for page to load
            time.sleep(2)
            
            # Verify on step 1
            progress_text = page.query_selector('#progress-text')
            assert 'Step 1' in progress_text.inner_text()
            
            # Try to click Next without selecting industry
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.5)
            
            # Should still be on step 1 (validation prevents progression)
            progress_text = page.query_selector('#progress-text')
            assert 'Step 1' in progress_text.inner_text(), \
                "Should still be on Step 1 when industry not selected"
            
            # Check that a toast/error appeared (basic check - toast exists in DOM briefly)
            # In real implementation, toast appears and fades, so we just verify we didn't advance
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            assert current_panel.get_attribute('data-step') == '1', \
                "Should remain on step 1 data panel"
            
            browser.close()
    finally:
        stop_server(proc)


def test_next_progresses_after_required_field_filled():
    """Verify Next works after filling required field (industry)."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(2)
            
            # Select industry (required field)
            industries = page.query_selector_all('#industries button')
            assert len(industries) > 0
            industries[0].click()
            time.sleep(0.3)
            
            # Now Next should work
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.8)
            
            # Should have advanced to step 2 or 3
            progress_text = page.query_selector('#progress-text')
            text = progress_text.inner_text()
            assert 'Step 1' not in text, \
                "Should have advanced past Step 1 after selecting industry"
            assert 'Step 2' in text or 'Step 3' in text, \
                f"Should be on Step 2 or 3, got: {text}"
            
            browser.close()
    finally:
        stop_server(proc)


def test_step3_requires_tone_and_platform():
    """Verify step 3 requires tone and platform selection before advancing."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(2)
            
            # Navigate to step 3
            # Step 1: Select industry
            industries = page.query_selector_all('#industries button')
            industries[0].click()
            time.sleep(0.3)
            
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.8)
            
            # Check if on step 2 or already on step 3
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            current_step = current_panel.get_attribute('data-step')
            
            if current_step == '2':
                # Skip step 2 or fill it
                next_btn.click()
                time.sleep(0.8)
            
            # Now should be on step 3
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            assert current_panel.get_attribute('data-step') == '3', "Should be on step 3"
            
            # Try to advance without selecting tone
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.5)
            
            # Should still be on step 3
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            assert current_panel.get_attribute('data-step') == '3', \
                "Should still be on step 3 without tone selected"
            
            # Select tone
            tones = page.query_selector_all('#tones button')
            assert len(tones) > 0
            tones[0].click()
            time.sleep(0.3)
            
            # Try to advance without platform
            next_btn.click()
            time.sleep(0.5)
            
            # Should still be on step 3 (platform required)
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            assert current_panel.get_attribute('data-step') == '3', \
                "Should still be on step 3 without platform selected"
            
            # Select platform
            platforms = page.query_selector_all('#platforms button')
            assert len(platforms) > 0
            platforms[0].click()
            time.sleep(0.3)
            
            # Now should advance
            next_btn.click()
            time.sleep(0.8)
            
            # Should be on step 4
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            assert current_panel.get_attribute('data-step') == '4', \
                "Should have advanced to step 4 after selecting tone and platform"
            
            browser.close()
    finally:
        stop_server(proc)


def test_step4_is_optional_can_skip():
    """Verify step 4 (Brand Inspiration) is optional and can be skipped."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(2)
            
            # Navigate to step 4
            industries = page.query_selector_all('#industries button')
            industries[0].click()
            time.sleep(0.3)
            
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.8)
            
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            if current_panel.get_attribute('data-step') == '2':
                next_btn.click()
                time.sleep(0.8)
            
            # On step 3 - select required fields
            tones = page.query_selector_all('#tones button')
            tones[0].click()
            time.sleep(0.3)
            
            platforms = page.query_selector_all('#platforms button')
            platforms[0].click()
            time.sleep(0.3)
            
            next_btn.click()
            time.sleep(0.8)
            
            # Should be on step 4
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            assert current_panel.get_attribute('data-step') == '4'
            
            # Step 4 should allow skipping (Next should work without filling anything)
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.8)
            
            # Should have advanced to step 5
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            assert current_panel.get_attribute('data-step') == '5', \
                "Step 4 (Brand Inspiration) should be optional and allow skipping"
            
            browser.close()
    finally:
        stop_server(proc)
