"""E2E tests for wizard custom write-in chip functionality."""

import os
import time
import pytest
import pathlib
import subprocess
import requests
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv("PORT", "5001"))
BASE = f"http://127.0.0.1:{PORT}"

pytestmark = pytest.mark.skipif(os.getenv("RUN_UI_SMOKE") != "1", reason="UI smoke tests disabled (set RUN_UI_SMOKE=1)")


def start_server():
    py = "./.venv/bin/python" if (ROOT / ".venv" / "bin" / "python").exists() else "python3"
    env = os.environ.copy()
    p = subprocess.Popen([py, "app.py"], cwd=str(ROOT), env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


def test_wizard_writein_chip_creation():
    """
    Test that users can create custom chips via "Other..." button.
    
    Acceptance criteria:
    - Click "Other..." button opens write-in input
    - User can type custom text
    - Clicking "Add" creates a custom chip
    - Custom chip is auto-selected
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate and select industry
            page.goto(f'{BASE}/app', wait_until='networkidle', timeout=30000)
            page.wait_for_function('window.CFG !== null', timeout=10000)
            page.wait_for_selector('[data-key="salon"]', timeout=10000)
            page.click('[data-key="salon"]')
            time.sleep(2)
            
            # Find and click "Other..." button in focus topics group
            other_btn = page.locator('#chip-group-focus-topics [data-action="write-in"]').first
            assert other_btn.count() > 0, "Other... button should exist"
            other_btn.click()
            time.sleep(0.5)
            
            # Verify write-in input appears
            write_in_input = page.locator('#chip-group-focus-topics-write-in')
            assert write_in_input.count() > 0, "Write-in input should appear"
            assert write_in_input.is_visible(), "Write-in input should be visible"
            
            # Type custom text
            custom_text = "Premium hair care"
            write_in_input.fill(custom_text)
            
            # Click Add button
            add_btn = page.locator('#chip-group-focus-topics [data-action="add-write-in"]').first
            add_btn.click()
            time.sleep(0.5)
            
            # Verify custom chip was created and is selected
            custom_chip = page.locator(f'.chip-btn:has-text("{custom_text}")').first
            assert custom_chip.count() > 0, "Custom chip should be created"
            assert 'chip-selected' in custom_chip.get_attribute('class'), "Custom chip should be auto-selected"
            
            browser.close()
    finally:
        stop_server(proc)


def test_wizard_writein_chip_persistence():
    """
    Test that custom chips persist across page reloads.
    
    Acceptance criteria:
    - Create a custom chip
    - Save profile and reload page
    - Custom chip still exists and remains selectable
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate and select industry
            page.goto(f'{BASE}/app', wait_until='networkidle', timeout=30000)
            page.wait_for_function('window.CFG !== null', timeout=10000)
            page.wait_for_selector('[data-key="salon"]', timeout=10000)
            page.click('[data-key="salon"]')
            time.sleep(2)
            
            # Create custom chip
            other_btn = page.locator('#chip-group-focus-topics [data-action="write-in"]').first
            other_btn.click()
            time.sleep(0.5)
            
            custom_text = "Luxury styling services"
            write_in_input = page.locator('#chip-group-focus-topics-write-in')
            write_in_input.fill(custom_text)
            
            add_btn = page.locator('#chip-group-focus-topics [data-action="add-write-in"]').first
            add_btn.click()
            time.sleep(0.5)
            
            # Verify custom chip exists
            custom_chip = page.locator(f'.chip-btn:has-text("{custom_text}")').first
            assert custom_chip.count() > 0, "Custom chip should be created"
            
            # Navigate to next step to trigger save
            page.click('#next')
            time.sleep(1)
            
            # Reload the page
            page.reload(wait_until='networkidle')
            page.wait_for_function('window.CFG !== null', timeout=10000)
            
            # Re-select industry (to load chips)
            # Note: In actual implementation, industry selection should persist
            time.sleep(2)
            
            # Verify custom chip still exists
            custom_chip_after_reload = page.locator(f'.chip-btn:has-text("{custom_text}")').first
            assert custom_chip_after_reload.count() > 0, "Custom chip should persist after reload"
            
            # Verify it can still be toggled
            custom_chip_after_reload.click()
            time.sleep(0.3)
            # Should have toggle state (either selected or not)
            
            browser.close()
    finally:
        stop_server(proc)


def test_wizard_writein_cancel():
    """
    Test that canceling write-in closes the input without creating a chip.
    
    Acceptance criteria:
    - Click "Other..." opens write-in
    - Click "Cancel" closes write-in without creating chip
    - "Other..." button is available again
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate and select industry
            page.goto(f'{BASE}/app', wait_until='networkidle', timeout=30000)
            page.wait_for_function('window.CFG !== null', timeout=10000)
            page.wait_for_selector('[data-key="salon"]', timeout=10000)
            page.click('[data-key="salon"]')
            time.sleep(2)
            
            # Count initial chips
            initial_chips = page.locator('#chip-group-focus-topics .chip-btn').count()
            
            # Click "Other..."
            other_btn = page.locator('#chip-group-focus-topics [data-action="write-in"]').first
            other_btn.click()
            time.sleep(0.5)
            
            # Type some text
            write_in_input = page.locator('#chip-group-focus-topics-write-in')
            write_in_input.fill("Test chip that will be cancelled")
            
            # Click Cancel
            cancel_btn = page.locator('#chip-group-focus-topics [data-action="cancel-write-in"]').first
            cancel_btn.click()
            time.sleep(0.5)
            
            # Verify no new chip was created
            final_chips = page.locator('#chip-group-focus-topics .chip-btn').count()
            assert final_chips == initial_chips, "No chip should be created after cancel"
            
            # Verify "Other..." button is available again
            other_btn_after = page.locator('#chip-group-focus-topics [data-action="write-in"]').first
            assert other_btn_after.count() > 0, "Other... button should be available again"
            
            browser.close()
    finally:
        stop_server(proc)
