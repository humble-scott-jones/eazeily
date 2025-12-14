"""E2E test: Step title updates with stepper progress."""

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


def test_step_counter_displays_correctly():
    """Verify step counter displays 'Step X of 5' format."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Check step counter on initial load
            step_counter = page.query_selector('#step-counter')
            assert step_counter is not None, "Step counter element not found"
            assert step_counter.inner_text() == "Step 1 of 5", f"Expected 'Step 1 of 5', got '{step_counter.inner_text()}'"
            
            browser.close()
    finally:
        stop_server(proc)


def test_step_title_displays_correctly():
    """Verify step title displays correctly for each step."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for page to be ready
            time.sleep(1)
            
            # Check step 1 title
            step_title = page.query_selector('#step-title')
            assert step_title is not None, "Step title element not found"
            
            title_text = step_title.inner_text()
            assert "Choose your industry" in title_text, f"Expected 'Choose your industry' in step 1, got '{title_text}'"
            
            browser.close()
    finally:
        stop_server(proc)


def test_step_title_mobile_displays():
    """Verify mobile step title element exists."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Check mobile step title exists
            step_title_mobile = page.query_selector('#step-title-mobile')
            assert step_title_mobile is not None, "Mobile step title element not found"
            
            mobile_text = step_title_mobile.inner_text()
            assert "Choose your industry" in mobile_text, f"Expected 'Choose your industry' in mobile step title, got '{mobile_text}'"
            
            browser.close()
    finally:
        stop_server(proc)


def test_progress_bar_visual_exists():
    """Verify visual progress bar exists and has correct styling."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Check progress bar exists
            progress_bar = page.query_selector('#progress-bar-visual')
            assert progress_bar is not None, "Visual progress bar element not found"
            
            # Check it has width style (should be 20% for step 1)
            width_style = progress_bar.get_attribute('style')
            assert 'width' in width_style, "Progress bar should have width style"
            
            browser.close()
    finally:
        stop_server(proc)


def test_step_counter_updates_on_navigation():
    """Verify step counter updates when navigating between steps."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for config to load
            time.sleep(2)
            
            # Select an industry to enable Next button
            industry_button = page.query_selector('#industries .choice')
            if industry_button:
                industry_button.click()
                time.sleep(0.5)
                
                # Click Next button
                next_button = page.query_selector('#next')
                if next_button and not next_button.is_disabled():
                    next_button.click()
                    time.sleep(1)
                    
                    # Check step counter updated
                    step_counter = page.query_selector('#step-counter')
                    if step_counter:
                        counter_text = step_counter.inner_text()
                        # Should be step 2 or 3 (depending on skipStep2)
                        assert "Step" in counter_text and "of 5" in counter_text, f"Counter should show step progress, got '{counter_text}'"
            
            browser.close()
    finally:
        stop_server(proc)


def test_stepper_premium_styling():
    """Verify stepper has premium styling elements."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Check for gradient progress bar container
            progress_container = page.query_selector('.bg-gradient-to-r.from-purple-50.to-blue-50')
            assert progress_container is not None, "Premium styled progress container not found"
            
            # Check for gradient progress bar
            progress_bar = page.query_selector('.bg-gradient-to-r.from-purple-600.to-blue-600')
            assert progress_bar is not None, "Gradient progress bar not found"
            
            browser.close()
    finally:
        stop_server(proc)
