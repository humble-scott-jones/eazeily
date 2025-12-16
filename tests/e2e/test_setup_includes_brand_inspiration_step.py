"""E2E test: Setup wizard includes Brand Inspiration step and navigation works."""

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


def test_setup_wizard_has_five_steps():
    """Verify setup wizard displays 5 steps including Brand Inspiration."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Check that there are 5 step indicators
            step_indicators = page.query_selector_all('.steps .step')
            assert len(step_indicators) == 5, f"Expected 5 steps, found {len(step_indicators)}"
            
            browser.close()
    finally:
        stop_server(proc)


def test_brand_inspiration_step_exists():
    """Verify Brand Inspiration step panel exists with correct content."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Find the step 4 panel (Brand Inspiration)
            brand_step = page.query_selector('.step-panel[data-step="4"]')
            assert brand_step is not None, "Brand Inspiration step panel not found"
            
            # Verify it has the right heading
            heading = brand_step.query_selector('h2')
            assert heading is not None
            assert 'Brand Inspiration' in heading.inner_text()
            
            browser.close()
    finally:
        stop_server(proc)


def test_brand_inspiration_step_has_inputs():
    """Verify Brand Inspiration step has expected input fields."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Check for brand inspiration input containers
            brand_container = page.query_selector('#wizard-brand-inspirations')
            assert brand_container is not None, "Brand inspirations container not found"
            
            anti_brand_container = page.query_selector('#wizard-brand-anti-inspirations')
            assert anti_brand_container is not None, "Anti-brand inspirations container not found"
            
            # Check for add brand button
            add_brand_btn = page.query_selector('#wizard-add-brand-btn')
            assert add_brand_btn is not None, "Add brand button not found"
            
            # Check for vibe preset buttons
            vibe_btns = page.query_selector_all('.wizard-vibe-preset-btn')
            assert len(vibe_btns) >= 5, "Expected at least 5 vibe preset buttons"
            
            browser.close()
    finally:
        stop_server(proc)


def test_brand_inspiration_has_initial_input():
    """Verify Brand Inspiration step initializes with one brand input field."""
    proc = start_server()
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{BASE}/app", wait_until="networkidle")
            
            # Wait a moment for JavaScript to initialize
            time.sleep(1)
            
            # Check that there's at least one brand name input
            brand_inputs = page.query_selector_all('#wizard-brand-inspirations .brand-name')
            assert len(brand_inputs) >= 1, "Expected at least one initial brand input field"
            
            browser.close()
    finally:
        stop_server(proc)
