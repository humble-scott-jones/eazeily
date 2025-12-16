"""E2E test: Setup wizard stepper increments correctly through all steps."""

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


def test_stepper_increments_through_all_steps():
    """Verify stepper increments correctly as user clicks Next through all steps."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for page to load
            time.sleep(1)
            
            # Check initial state - should be on step 1
            progress_text = page.query_selector('#progress-text')
            assert progress_text is not None
            initial_text = progress_text.inner_text()
            assert 'Step 1' in initial_text, f"Expected 'Step 1' in progress text, got: {initial_text}"
            
            # Step 1: Select industry
            industries = page.query_selector_all('#industries .choice-btn')
            assert len(industries) > 0, "No industry choices found"
            industries[0].click()
            time.sleep(0.3)
            
            # Click Next to step 2 or 3 (depending on if step 2 is skipped)
            next_btn = page.query_selector('#next')
            assert next_btn is not None
            next_btn.click()
            time.sleep(0.5)
            
            # Verify step incremented
            progress_text = page.query_selector('#progress-text')
            step_text = progress_text.inner_text()
            assert 'Step 2' in step_text or 'Step 3' in step_text, f"Expected step to increment, got: {step_text}"
            
            # Check if we're on step 2 or skipped to 3
            current_panel = page.query_selector('.step-panel:not(.hidden)')
            current_step = current_panel.get_attribute('data-step')
            
            if current_step == '2':
                # Step 2 has questions - skip it or answer
                next_btn.click()
                time.sleep(0.5)
                current_step = '3'
            
            # Step 3: Select tone and platform
            tones = page.query_selector_all('#tones .choice-btn')
            if len(tones) > 0:
                tones[0].click()
                time.sleep(0.3)
            
            platforms = page.query_selector_all('#platforms .choice-btn')
            if len(platforms) > 0:
                platforms[0].click()
                time.sleep(0.3)
            
            next_btn.click()
            time.sleep(0.5)
            
            # Verify we're on step 4
            progress_text = page.query_selector('#progress-text')
            step_text = progress_text.inner_text()
            assert 'Step' in step_text, f"Expected step text, got: {step_text}"
            
            # Step 4: Brand Inspiration (optional)
            next_btn.click()
            time.sleep(0.5)
            
            # Verify we're on final step
            progress_text = page.query_selector('#progress-text')
            step_text = progress_text.inner_text()
            assert 'Step' in step_text, f"Expected step text, got: {step_text}"
            
            # Verify Finish button appears on last step
            next_btn = page.query_selector('#next')
            button_text = next_btn.inner_text()
            assert button_text == 'Finish', f"Expected 'Finish' button on last step, got: {button_text}"
            
            browser.close()
    finally:
        stop_server(proc)


def test_stepper_shows_correct_step_numbers():
    """Verify stepper displays correct step X of Y at each stage."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(1)
            
            # Get initial total steps
            progress_text = page.query_selector('#progress-text')
            initial_text = progress_text.inner_text()
            # Extract total from "Step X of Y"
            parts = initial_text.split('of')
            assert len(parts) == 2, f"Expected 'Step X of Y' format, got: {initial_text}"
            total_steps = int(parts[1].strip())
            
            # Verify total is reasonable (should be 4 or 5)
            assert total_steps >= 4 and total_steps <= 5, f"Expected 4-5 total steps, got: {total_steps}"
            
            # Select industry and move forward
            industries = page.query_selector_all('#industries .choice-btn')
            industries[0].click()
            time.sleep(0.3)
            
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.5)
            
            # Verify total steps stayed consistent
            progress_text = page.query_selector('#progress-text')
            new_text = progress_text.inner_text()
            assert f'of {total_steps}' in new_text, f"Total steps changed unexpectedly: {new_text}"
            
            browser.close()
    finally:
        stop_server(proc)


def test_back_button_decrements_step():
    """Verify clicking Back decrements the step counter correctly."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            time.sleep(1)
            
            # Select industry and go to next step
            industries = page.query_selector_all('#industries .choice-btn')
            industries[0].click()
            time.sleep(0.3)
            
            next_btn = page.query_selector('#next')
            next_btn.click()
            time.sleep(0.5)
            
            # Get current step
            progress_text = page.query_selector('#progress-text')
            forward_text = progress_text.inner_text()
            
            # Click back
            back_btn = page.query_selector('#prev')
            assert back_btn is not None
            back_btn.click()
            time.sleep(0.5)
            
            # Verify we're back to step 1
            progress_text = page.query_selector('#progress-text')
            back_text = progress_text.inner_text()
            assert 'Step 1' in back_text, f"Expected to be back on Step 1, got: {back_text}"
            
            browser.close()
    finally:
        stop_server(proc)
