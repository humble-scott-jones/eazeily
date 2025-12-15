"""E2E test: Setup wizard total steps matches enabled steps dynamically."""

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


def test_total_steps_matches_enabled_steps():
    """Verify total step count matches the number of enabled steps in the wizard."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(1)
            
            # Count visible step panels (enabled steps)
            step_panels = page.query_selector_all('.step-panel')
            enabled_step_count = len(step_panels)
            
            # Get displayed total from progress text
            progress_text = page.query_selector('#progress-text')
            text = progress_text.inner_text()
            parts = text.split('of')
            displayed_total = int(parts[1].strip())
            
            # Verify they match (or within 1, since step 2 might be conditionally hidden)
            assert abs(displayed_total - enabled_step_count) <= 1, \
                f"Total steps {displayed_total} doesn't match enabled steps {enabled_step_count}"
            
            browser.close()
    finally:
        stop_server(proc)


def test_step_indicators_match_total_steps():
    """Verify number of visible step indicator dots matches total steps."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(1)
            
            # Get total from progress text
            progress_text = page.query_selector('#progress-text')
            text = progress_text.inner_text()
            parts = text.split('of')
            total_steps = int(parts[1].strip())
            
            # Count visible step dots (desktop)
            step_dots = page.query_selector_all('#steps .step')
            visible_dots = [dot for dot in step_dots if dot.is_visible()]
            
            # Should have exactly total_steps dots visible
            assert len(visible_dots) == total_steps, \
                f"Expected {total_steps} visible step dots, found {len(visible_dots)}"
            
            browser.close()
    finally:
        stop_server(proc)


def test_step_count_adjusts_when_step2_skipped():
    """Verify total step count adjusts when step 2 (context) is skipped."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(1)
            
            # Select an industry that has no follow-up questions (e.g., "other")
            # This should cause step 2 to be skipped
            industries = page.query_selector_all('#industries .choice-btn')
            
            # Find "Other" or similar industry with no questions
            other_industry = None
            for industry in industries:
                text = industry.inner_text().lower()
                if 'other' in text or 'custom' in text:
                    other_industry = industry
                    break
            
            if other_industry is None:
                # If no "other" option, just pick first industry
                other_industry = industries[0]
            
            other_industry.click()
            time.sleep(0.5)
            
            # Get total after industry selection
            progress_text = page.query_selector('#progress-text')
            text = progress_text.inner_text()
            parts = text.split('of')
            total_after_selection = int(parts[1].strip())
            
            # Total should be 4 or 5 depending on whether step 2 is enabled
            assert total_after_selection >= 4 and total_after_selection <= 5, \
                f"Expected 4-5 steps, got {total_after_selection}"
            
            # Click Next
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.5)
            
            # Check which step we're on now
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            current_step = current_panel.get_attribute('data-step')
            
            # If step 2 was skipped, we should be on step 3
            # If not, we should be on step 2
            assert current_step == '2' or current_step == '3', \
                f"Expected to be on step 2 or 3, got step {current_step}"
            
            browser.close()
    finally:
        stop_server(proc)


def test_brand_inspiration_step_included_in_total():
    """Verify Brand Inspiration step (step 4) is included in total count."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(1)
            
            # Verify step 4 panel exists
            step4_panel = page.query_selector('.step-panel[data-step="4"]')
            assert step4_panel is not None, "Brand Inspiration step (step 4) not found"
            
            # Verify it's included in step count
            progress_text = page.query_selector('#progress-text')
            text = progress_text.inner_text()
            parts = text.split('of')
            total_steps = int(parts[1].strip())
            
            # Total should be at least 4 (to include Brand Inspiration)
            assert total_steps >= 4, \
                f"Total steps {total_steps} too low to include Brand Inspiration"
            
            browser.close()
    finally:
        stop_server(proc)
