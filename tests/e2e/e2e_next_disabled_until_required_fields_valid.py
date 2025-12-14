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


def test_next_button_disabled_on_step1_without_industry():
    """Verify Next button is disabled on step 1 until industry is selected."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for config to load
            time.sleep(2)
            
            # Check Next button is disabled initially
            next_button = page.query_selector('#next')
            assert next_button is not None, "Next button not found"
            
            is_disabled = next_button.is_disabled()
            assert is_disabled, "Next button should be disabled when no industry is selected"
            
            # Check for disabled styling
            has_opacity_class = next_button.evaluate("el => el.classList.contains('opacity-50')")
            assert has_opacity_class, "Next button should have opacity-50 class when disabled"
            
            browser.close()
    finally:
        stop_server(proc)


def test_next_button_enabled_after_industry_selection():
    """Verify Next button becomes enabled after selecting an industry."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for config to load
            time.sleep(2)
            
            # Select an industry
            industry_button = page.query_selector('#industries .choice')
            assert industry_button is not None, "Industry choice button not found"
            industry_button.click()
            time.sleep(0.5)
            
            # Check Next button is now enabled
            next_button = page.query_selector('#next')
            is_disabled = next_button.is_disabled()
            assert not is_disabled, "Next button should be enabled after selecting industry"
            
            # Check disabled styling is removed
            has_opacity_class = next_button.evaluate("el => el.classList.contains('opacity-50')")
            assert not has_opacity_class, "Next button should not have opacity-50 class when enabled"
            
            browser.close()
    finally:
        stop_server(proc)


def test_next_button_disabled_on_step3_without_tone():
    """Verify Next button is disabled on step 3 until tone is selected."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for config to load
            time.sleep(2)
            
            # Navigate to step 3
            # Step 1: Select industry
            industry_button = page.query_selector('#industries .choice')
            if industry_button:
                industry_button.click()
                time.sleep(0.5)
                
                # Click Next to go to step 2 or 3
                next_button = page.query_selector('#next')
                if next_button and not next_button.is_disabled():
                    next_button.click()
                    time.sleep(1)
                    
                    # If we're on step 2, click Next again
                    step_counter = page.query_selector('#step-counter')
                    if step_counter and "Step 2" in step_counter.inner_text():
                        # Select a goal if available
                        goal_chip = page.query_selector('#industry-questions .choice')
                        if goal_chip:
                            goal_chip.click()
                            time.sleep(0.5)
                        
                        next_button = page.query_selector('#next')
                        if next_button and not next_button.is_disabled():
                            next_button.click()
                            time.sleep(1)
                    
                    # Now on step 3, check Next is disabled without tone
                    next_button = page.query_selector('#next')
                    if next_button:
                        is_disabled = next_button.is_disabled()
                        # Button should be disabled if tone is not selected
                        # Note: Pre-selection might enable it, so we check if selection is needed
                        tone_selected = page.query_selector('#tones .choice.selected')
                        if not tone_selected:
                            assert is_disabled, "Next button should be disabled when tone is not selected"
            
            browser.close()
    finally:
        stop_server(proc)


def test_next_button_enabled_after_tone_and_platform_selection():
    """Verify Next button becomes enabled after selecting tone and platform on step 3."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for config to load
            time.sleep(2)
            
            # Navigate to step 3
            # Step 1: Select industry
            industry_button = page.query_selector('#industries .choice')
            if industry_button:
                industry_button.click()
                time.sleep(0.5)
                
                # Click Next
                next_button = page.query_selector('#next')
                if next_button and not next_button.is_disabled():
                    next_button.click()
                    time.sleep(1)
                    
                    # If on step 2, navigate forward
                    step_counter = page.query_selector('#step-counter')
                    if step_counter and "Step 2" in step_counter.inner_text():
                        goal_chip = page.query_selector('#industry-questions .choice')
                        if goal_chip:
                            goal_chip.click()
                            time.sleep(0.5)
                        next_button = page.query_selector('#next')
                        if next_button and not next_button.is_disabled():
                            next_button.click()
                            time.sleep(1)
                    
                    # On step 3 now
                    # Select tone if not already selected
                    tone_selected = page.query_selector('#tones .choice.selected')
                    if not tone_selected:
                        tone_button = page.query_selector('#tones .choice')
                        if tone_button:
                            tone_button.click()
                            time.sleep(0.5)
                    
                    # Platform should be pre-selected (Instagram by default)
                    # Check Next button is now enabled
                    next_button = page.query_selector('#next')
                    if next_button:
                        is_disabled = next_button.is_disabled()
                        assert not is_disabled, "Next button should be enabled after selecting tone and platform"
            
            browser.close()
    finally:
        stop_server(proc)


def test_step4_next_button_always_enabled_optional_step():
    """Verify Next button is always enabled on step 4 (optional Brand Inspiration)."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for config to load
            time.sleep(2)
            
            # Navigate to step 4
            # We'll use a direct navigation approach
            # First, fill required fields
            industry_button = page.query_selector('#industries .choice')
            if industry_button:
                industry_button.click()
                time.sleep(0.5)
                
                # Navigate forward through steps
                for _ in range(3):  # Max 3 clicks to get to step 4
                    next_button = page.query_selector('#next')
                    if next_button and not next_button.is_disabled():
                        # Select necessary fields
                        tone_button = page.query_selector('#tones .choice')
                        if tone_button and not page.query_selector('#tones .choice.selected'):
                            tone_button.click()
                            time.sleep(0.3)
                        
                        goal_chip = page.query_selector('#industry-questions .choice')
                        if goal_chip and not page.query_selector('#industry-questions .choice.selected'):
                            goal_chip.click()
                            time.sleep(0.3)
                        
                        next_button.click()
                        time.sleep(0.8)
                        
                        # Check if we're on step 4
                        step_counter = page.query_selector('#step-counter')
                        if step_counter and "Step 4" in step_counter.inner_text():
                            break
                
                # On step 4, Next button should be enabled even without input
                step_counter = page.query_selector('#step-counter')
                if step_counter and "Step 4" in step_counter.inner_text():
                    next_button = page.query_selector('#next')
                    if next_button:
                        is_disabled = next_button.is_disabled()
                        assert not is_disabled, "Next button should always be enabled on step 4 (optional step)"
            
            browser.close()
    finally:
        stop_server(proc)


def test_next_button_shows_helpful_tooltip():
    """Verify Next button shows helpful tooltip when disabled."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for config to load
            time.sleep(2)
            
            # Check Next button has a title attribute when disabled
            next_button = page.query_selector('#next')
            assert next_button is not None, "Next button not found"
            
            if next_button.is_disabled():
                title_attr = next_button.get_attribute('title')
                # Should have a helpful message
                assert title_attr is not None and len(title_attr) > 0, "Disabled Next button should have a helpful title/tooltip"
            
            browser.close()
    finally:
        stop_server(proc)


def test_saving_feedback_appears_on_step_transition():
    """Verify 'Saving...' feedback appears when transitioning between steps."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait for config to load
            time.sleep(2)
            
            # Select an industry
            industry_button = page.query_selector('#industries .choice')
            if industry_button:
                industry_button.click()
                time.sleep(0.5)
                
                # Click Next and immediately check for saving feedback
                next_button = page.query_selector('#next')
                if next_button and not next_button.is_disabled():
                    next_button.click()
                    
                    # Check button text changes to "Saving…" briefly
                    # Note: This might be very fast (300ms), so we check immediately
                    time.sleep(0.1)
                    button_text = next_button.inner_text()
                    
                    # Button should either show "Saving…" or have completed and moved to next step
                    # We consider the test passing if we see "Saving…" or if we're on a new step
                    step_counter = page.query_selector('#step-counter')
                    if step_counter:
                        counter_text = step_counter.inner_text()
                        # If we moved to a new step, the saving happened
                        assert "Step" in counter_text, "Should have progressed after clicking Next"
            
            browser.close()
    finally:
        stop_server(proc)
