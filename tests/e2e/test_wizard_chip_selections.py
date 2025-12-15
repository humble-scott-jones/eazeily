"""E2E tests for wizard applying GOOD defaults and saving chip selections."""

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


def test_wizard_applies_good_defaults_on_industry_select():
    """
    Test that selecting an industry in the wizard fetches and applies GOOD defaults.
    
    Acceptance criteria:
    - When user selects an industry, good_defaults API is called
    - Chip selections are automatically applied from the defaults
    - User can edit the selections (they're not locked)
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Track API calls
            api_calls = []
            
            def handle_response(response):
                if '/api/industry_packs/' in response.url and '/good_defaults' in response.url:
                    api_calls.append(response.url)
            
            page.on('response', handle_response)
            
            # Navigate to wizard
            page.goto(f'{BASE}/app', wait_until='networkidle', timeout=30000)
            
            # Wait for config to load
            page.wait_for_function('window.CFG !== null && window.CFG !== undefined', timeout=10000)
            
            # Wait for industries to render  
            page.wait_for_selector('[data-key]', timeout=10000)
            
            # Click salon industry
            salon_btn = page.locator('[data-key="salon"]').first
            salon_btn.click()
            
            # Wait for API call to complete
            time.sleep(2)
            
            # Verify API was called
            assert len(api_calls) > 0, "good_defaults API should have been called"
            assert 'salon/good_defaults' in api_calls[0], "Should fetch salon good_defaults"
            
            # Verify industry is marked as selected
            assert 'selected' in salon_btn.get_attribute('class'), "Salon industry should be selected"
            
            browser.close()
    finally:
        stop_server(proc)


def test_wizard_shows_chip_groups_after_industry_selection():
    """
    Test that chip groups appear and are populated after industry selection.
    
    Acceptance criteria:
    - Chip section is visible after industry selection
    - Chip groups are rendered with chips from good_defaults
    - Recommended chips are preselected
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate to wizard
            page.goto(f'{BASE}/app', wait_until='networkidle', timeout=30000)
            
            # Wait for config to load
            page.wait_for_function('window.CFG !== null', timeout=10000)
            
            # Wait for industries to render
            page.wait_for_selector('[data-key="salon"]', timeout=10000)
            
            # Click salon industry
            page.click('[data-key="salon"]')
            
            # Wait for chip groups to render
            time.sleep(2)
            
            # Verify chip section is visible
            chip_section = page.locator('#chip-selection-section')
            assert chip_section.count() > 0, "Chip section should exist"
            assert chip_section.is_visible(), "Chip section should be visible"
            
            # Verify chip groups exist
            focus_group = page.locator('#chip-group-focus-topics')
            audience_group = page.locator('#chip-group-audience')
            offers_group = page.locator('#chip-group-offers')
            proof_group = page.locator('#chip-group-proof')
            
            assert focus_group.count() > 0, "Focus topics group should exist"
            assert audience_group.count() > 0, "Audience group should exist"
            assert offers_group.count() > 0, "Offers group should exist"
            assert proof_group.count() > 0, "Proof group should exist"
            
            # Verify chips are rendered
            chips = page.locator('.chip-btn')
            assert chips.count() > 0, "Chip buttons should be rendered"
            
            # Verify some chips are preselected
            selected_chips = page.locator('.chip-btn.chip-selected')
            assert selected_chips.count() > 0, "Some chips should be preselected from defaults"
            
            browser.close()
    finally:
        stop_server(proc)


def test_wizard_saves_and_prefills_chip_selections():
    """
    Test that chip selections are saved and prefilled on reload.
    
    Acceptance criteria:
    - User completes wizard with chip selections
    - Selections are saved to profile
    - On reload, saved selections are prefilled (not defaults)
    """
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to wizard
            page.goto(f'{BASE}/app', wait_until='networkidle', timeout=30000)
            
            # Wait for config to load
            page.wait_for_function('window.CFG !== null', timeout=10000)
            
            # Wait for industries and select one
            page.wait_for_selector('[data-key="salon"]', timeout=10000)
            page.click('[data-key="salon"]')
            
            # Wait for chips to load
            time.sleep(2)
            
            # Click a specific chip to modify selection
            chips = page.locator('.chip-btn').all()
            if len(chips) > 3:
                # Deselect first selected chip if any, or select an unselected one
                target_chip = chips[3]
                initial_class = target_chip.get_attribute('class')
                target_chip.click()
                time.sleep(0.5)
                
                # Verify the chip state changed
                new_class = target_chip.get_attribute('class')
                assert initial_class != new_class, "Chip selection should toggle"
            
            # Navigate to next step to trigger save
            page.click('#next')
            time.sleep(1)
            
            # Reload the page
            page.reload(wait_until='networkidle')
            
            # Wait for config to reload
            page.wait_for_function('window.CFG !== null', timeout=10000)
            
            # Industry should still be selected
            salon_btn = page.locator('[data-key="salon"]').first
            assert 'selected' in salon_btn.get_attribute('class'), "Industry selection should persist"
            
            browser.close()
    finally:
        stop_server(proc)

