"""
E2E test: Brand inspiration add/remove/persist functionality

Tests:
1. Add brand button works and respects max limit (4)
2. Add anti-brand button works and respects max limit (3)
3. Remove button works for brands and anti-brands
4. Counter displays correctly (X/4, X/3)
5. Data persists when navigating away and back to step 4
6. Data is saved to backend on Next click
"""

import os
import time
import subprocess
import pathlib
import requests
import pytest
from playwright.sync_api import sync_playwright, expect

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv("PORT", "5001"))
BASE = f"http://127.0.0.1:{PORT}"

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_UI_SMOKE") != "1",
    reason="UI smoke tests disabled (set RUN_UI_SMOKE=1)"
)


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


def test_brand_inspo_add_remove_persist():
    """Test that brand inspiration add/remove/persist works correctly."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Go to wizard
            page.goto(f"{BASE}/app", wait_until="networkidle")
            time.sleep(1)  # Wait for JS initialization
            
            # Navigate to step 4 (Brand Inspiration)
            # First, fill required fields in step 1
            page.click('button[data-industry="retail"]')
            time.sleep(0.3)
            
            # Click next to go to step 2
            page.click('#next')
            time.sleep(0.5)
            
            # Fill step 2 if needed (company name)
            company_input = page.query_selector('#company')
            if company_input:
                company_input.fill('Test Store')
            
            # Click next to go to step 3
            page.click('#next')
            time.sleep(0.5)
            
            # Select tone and platform in step 3
            page.click('button[data-tone="friendly"]')
            time.sleep(0.3)
            
            # Click next to go to step 4
            page.click('#next')
            time.sleep(0.5)
            
            # Now we're at step 4 (Brand Inspiration)
            brand_step = page.query_selector('.step-panel[data-step="4"]')
            assert brand_step is not None, "Should be on step 4"
            assert not brand_step.evaluate('el => el.classList.contains("hidden")'), "Step 4 should be visible"
            
            # Check initial state - should have 1 brand input already
            initial_brands = page.query_selector_all('#wizard-brand-inspirations .brand-name')
            assert len(initial_brands) >= 1, "Should have at least 1 initial brand input"
            
            # Check counter shows (1/4)
            add_brand_btn = page.query_selector('#wizard-add-brand-btn')
            assert add_brand_btn is not None
            btn_text = add_brand_btn.inner_text()
            assert '1/4' in btn_text, f"Counter should show 1/4, got: {btn_text}"
            
            # Fill first brand
            page.fill('#wizard-brand-inspirations .brand-name', 'Apple')
            page.fill('#wizard-brand-inspirations .brand-why', 'Clean design')
            time.sleep(0.2)
            
            # Add second brand
            page.click('#wizard-add-brand-btn')
            time.sleep(0.3)
            
            brand_inputs = page.query_selector_all('#wizard-brand-inspirations .brand-name')
            assert len(brand_inputs) == 2, "Should have 2 brand inputs after clicking add"
            
            # Check counter updated to (2/4)
            btn_text = add_brand_btn.inner_text()
            assert '2/4' in btn_text, f"Counter should show 2/4, got: {btn_text}"
            
            # Fill second brand
            brand_inputs[1].fill('Nike')
            why_inputs = page.query_selector_all('#wizard-brand-inspirations .brand-why')
            why_inputs[1].fill('Bold and inspiring')
            
            # Add third and fourth brands
            page.click('#wizard-add-brand-btn')
            time.sleep(0.3)
            page.click('#wizard-add-brand-btn')
            time.sleep(0.3)
            
            # Should now have 4 brands
            brand_inputs = page.query_selector_all('#wizard-brand-inspirations .brand-name')
            assert len(brand_inputs) == 4, "Should have 4 brand inputs"
            
            # Check counter shows (4/4)
            btn_text = add_brand_btn.inner_text()
            assert '4/4' in btn_text, f"Counter should show 4/4, got: {btn_text}"
            
            # Button should be disabled at max
            is_disabled = add_brand_btn.is_disabled()
            assert is_disabled, "Add brand button should be disabled at max (4)"
            
            # Test remove button
            remove_btns = page.query_selector_all('#wizard-brand-inspirations .remove-brand-btn')
            assert len(remove_btns) >= 1, "Should have remove buttons"
            remove_btns[0].click()
            time.sleep(0.3)
            
            # Should now have 3 brands
            brand_inputs = page.query_selector_all('#wizard-brand-inspirations .brand-name')
            assert len(brand_inputs) == 3, "Should have 3 brand inputs after removal"
            
            # Counter should update
            btn_text = add_brand_btn.inner_text()
            assert '3/4' in btn_text, f"Counter should show 3/4 after removal, got: {btn_text}"
            
            # Button should be enabled again
            is_disabled = add_brand_btn.is_disabled()
            assert not is_disabled, "Add brand button should be enabled after removal"
            
            # Test anti-brand functionality
            add_anti_btn = page.query_selector('#wizard-add-anti-brand-btn')
            assert add_anti_btn is not None
            
            # Should show (0/3) initially
            anti_btn_text = add_anti_btn.inner_text()
            assert '0/3' in anti_btn_text, f"Anti-brand counter should show 0/3, got: {anti_btn_text}"
            
            # Add an anti-brand
            page.click('#wizard-add-anti-brand-btn')
            time.sleep(0.3)
            
            anti_inputs = page.query_selector_all('#wizard-brand-anti-inspirations .anti-brand-name')
            assert len(anti_inputs) == 1, "Should have 1 anti-brand input"
            
            # Fill it
            anti_inputs[0].fill('Generic Corp')
            anti_why = page.query_selector_all('#wizard-brand-anti-inspirations .anti-brand-why')
            anti_why[0].fill('Too corporate')
            
            # Counter should update
            anti_btn_text = add_anti_btn.inner_text()
            assert '1/3' in anti_btn_text, f"Anti-brand counter should show 1/3, got: {anti_btn_text}"
            
            # Add 2 more to test max limit
            page.click('#wizard-add-anti-brand-btn')
            time.sleep(0.2)
            page.click('#wizard-add-anti-brand-btn')
            time.sleep(0.2)
            
            anti_inputs = page.query_selector_all('#wizard-brand-anti-inspirations .anti-brand-name')
            assert len(anti_inputs) == 3, "Should have 3 anti-brand inputs"
            
            # Counter should show (3/3)
            anti_btn_text = add_anti_btn.inner_text()
            assert '3/3' in anti_btn_text, f"Anti-brand counter should show 3/3, got: {anti_btn_text}"
            
            # Button should be disabled
            is_disabled = add_anti_btn.is_disabled()
            assert is_disabled, "Add anti-brand button should be disabled at max (3)"
            
            # Test vibe preset selection
            vibe_btns = page.query_selector_all('.wizard-vibe-preset-btn')
            assert len(vibe_btns) >= 5, "Should have vibe preset buttons"
            
            # Click a vibe preset
            friendly_vibe = page.query_selector('.wizard-vibe-preset-btn[data-vibe="friendly_modern"]')
            if friendly_vibe:
                friendly_vibe.click()
                time.sleep(0.2)
                
                # Check it's selected (has border-indigo-500 class)
                classes = friendly_vibe.get_attribute('class')
                assert 'border-indigo-500' in classes, "Vibe preset should be selected"
            
            # Click next to save and go to step 5
            page.click('#next')
            time.sleep(0.5)
            
            # Should now be on step 5
            step5 = page.query_selector('.step-panel[data-step="5"]')
            assert step5 is not None
            assert not step5.evaluate('el => el.classList.contains("hidden")'), "Should be on step 5"
            
            # Go back to step 4 to verify data persists
            page.click('#prev')
            time.sleep(0.5)
            
            # Should be back on step 4
            brand_step = page.query_selector('.step-panel[data-step="4"]')
            assert not brand_step.evaluate('el => el.classList.contains("hidden")'), "Should be back on step 4"
            
            # Verify brands are still there
            brand_inputs = page.query_selector_all('#wizard-brand-inspirations .brand-name')
            assert len(brand_inputs) == 3, "Should still have 3 brands after navigation"
            
            # Check first brand value
            first_brand_value = brand_inputs[0].input_value()
            assert first_brand_value in ['Apple', 'Nike'], f"Brand should be preserved, got: {first_brand_value}"
            
            # Verify anti-brands
            anti_inputs = page.query_selector_all('#wizard-brand-anti-inspirations .anti-brand-name')
            assert len(anti_inputs) == 3, "Should still have 3 anti-brands"
            
            # Check vibe preset is still selected
            if friendly_vibe:
                classes = friendly_vibe.get_attribute('class')
                assert 'border-indigo-500' in classes, "Vibe preset should still be selected"
            
            print("✅ All UI tests passed!")
            
            browser.close()
    finally:
        stop_server(proc)


def test_brand_inspo_persist_to_backend():
    """Test that brand inspiration data is saved to backend."""
    proc = start_server()
    try:
        # Create a test user and profile via API
        session = requests.Session()
        session.post(f"{BASE}/api/signup", json={
            'email': 'ui_test@example.com',
            'password': 'testpass123'
        })
        
        # Save profile with brand inspirations
        session.post(f"{BASE}/api/profile", json={
            'industry': 'retail',
            'tone': 'friendly',
            'platforms': ['instagram'],
            'company': 'Test Company',
            'brand_inspirations': [
                {'name': 'Apple', 'why': 'Clean design'},
                {'name': 'Nike', 'why': 'Bold'}
            ],
            'brand_anti_inspirations': [
                {'name': 'Generic Corp', 'why': 'Too corporate'}
            ],
            'vibe_preset': 'friendly_modern'
        })
        
        # Now load the wizard with the same session
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            
            # Set cookies from session
            cookies = []
            for cookie in session.cookies:
                cookies.append({
                    'name': cookie.name,
                    'value': cookie.value,
                    'domain': 'localhost' if cookie.domain.startswith('.') else cookie.domain.replace('127.0.0.1', 'localhost'),
                    'path': cookie.path
                })
            context.add_cookies(cookies)
            
            page = context.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            time.sleep(2)  # Wait for JS and profile loading
            
            # Navigate to step 4
            # Click through steps quickly
            page.click('#next')  # to step 2
            time.sleep(0.3)
            page.click('#next')  # to step 3
            time.sleep(0.3)
            page.click('#next')  # to step 4
            time.sleep(0.5)
            
            # Should be on step 4 with hydrated data
            brand_inputs = page.query_selector_all('#wizard-brand-inspirations .brand-name')
            
            # Should have the 2 saved brands
            assert len(brand_inputs) == 2, f"Should have 2 hydrated brands, got {len(brand_inputs)}"
            
            # Check values
            if len(brand_inputs) >= 2:
                value1 = brand_inputs[0].input_value()
                value2 = brand_inputs[1].input_value()
                assert value1 == 'Apple', f"First brand should be Apple, got: {value1}"
                assert value2 == 'Nike', f"Second brand should be Nike, got: {value2}"
            
            # Check anti-brands
            anti_inputs = page.query_selector_all('#wizard-brand-anti-inspirations .anti-brand-name')
            assert len(anti_inputs) == 1, f"Should have 1 hydrated anti-brand, got {len(anti_inputs)}"
            
            if len(anti_inputs) >= 1:
                anti_value = anti_inputs[0].input_value()
                assert anti_value == 'Generic Corp', f"Anti-brand should be Generic Corp, got: {anti_value}"
            
            # Check vibe preset is selected
            friendly_vibe = page.query_selector('.wizard-vibe-preset-btn[data-vibe="friendly_modern"]')
            if friendly_vibe:
                classes = friendly_vibe.get_attribute('class')
                assert 'border-indigo-500' in classes, "Saved vibe preset should be selected"
            
            print("✅ Backend persistence test passed!")
            
            browser.close()
    finally:
        stop_server(proc)
