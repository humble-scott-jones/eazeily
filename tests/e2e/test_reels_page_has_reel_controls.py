"""
E2E test to verify that /generate/reels has all reel-specific controls.

Tests acceptance criteria:
- /generate/reels loads successfully
- Hook style selector exists
- Duration selector exists
- Shot list toggle exists
- On-screen text toggle exists
"""

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

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_UI_SMOKE") != "1", 
    reason="UI smoke tests disabled (set RUN_UI_SMOKE=1)"
)


def start_server():
    """Start Flask server and wait for it to be ready."""
    py = "./.venv/bin/python" if (ROOT / ".venv" / "bin" / "python").exists() else "python3"
    env = os.environ.copy()
    env['PORT'] = str(PORT)
    p = subprocess.Popen([py, "app.py"], cwd=str(ROOT), env=env)
    
    # Wait for server to be ready
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
    """Stop Flask server gracefully."""
    try:
        p.terminate()
        p.wait(timeout=5)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def test_reels_page_has_reel_controls():
    """
    Test that /generate/reels has all the expected reel-specific controls.
    
    Verifies:
    - Page loads successfully
    - Hook style selector exists
    - Format selector exists
    - Duration selector exists
    - Shot list toggle exists
    - On-screen text toggle exists
    - Generate button exists
    """
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to /generate/reels
            page.goto(f"{BASE}/generate/reels", wait_until="networkidle", timeout=10000)
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Check for hook style selector
            hook_style = page.query_selector("#hook-style")
            assert hook_style is not None, "Hook style selector should exist"
            
            # Check for format selector
            format_select = page.query_selector("#format")
            assert format_select is not None, "Format selector should exist"
            
            # Check for duration selector
            duration = page.query_selector("#duration")
            assert duration is not None, "Duration selector should exist"
            
            # Check for shot list toggle
            shot_list_toggle = page.query_selector("#include-shot-list")
            assert shot_list_toggle is not None, "Shot list toggle should exist"
            
            # Check for on-screen text toggle
            on_screen_text_toggle = page.query_selector("#include-on-screen-text")
            assert on_screen_text_toggle is not None, "On-screen text toggle should exist"
            
            # Check for generate button
            generate_btn = page.query_selector("#generate-btn")
            assert generate_btn is not None, "Generate button should exist"
            
            browser.close()
    
    finally:
        stop_server(proc)


def test_reels_page_has_script_structure():
    """
    Test that /generate/reels displays the script structure sections.
    
    Verifies:
    - Script structure container exists
    - Hook section exists
    - Beats section exists
    - CTA section exists
    - Caption section exists
    - Hashtags section exists
    """
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to /generate/reels
            page.goto(f"{BASE}/generate/reels", wait_until="networkidle", timeout=10000)
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Check for script sections container
            sections_container = page.query_selector("#reels-sections")
            assert sections_container is not None, "Script sections container should exist"
            
            # Check for individual sections
            hook_section = page.query_selector('[data-section="hook"]')
            assert hook_section is not None, "Hook section should exist"
            
            beats_section = page.query_selector('[data-section="beats"]')
            assert beats_section is not None, "Beats section should exist"
            
            cta_section = page.query_selector('[data-section="cta"]')
            assert cta_section is not None, "CTA section should exist"
            
            caption_section = page.query_selector('[data-section="caption"]')
            assert caption_section is not None, "Caption section should exist"
            
            hashtags_section = page.query_selector('[data-section="hashtags"]')
            assert hashtags_section is not None, "Hashtags section should exist"
            
            browser.close()
    
    finally:
        stop_server(proc)


def test_reels_page_title():
    """
    Test that /generate/reels has the correct page title and heading.
    
    Verifies:
    - Page title mentions Reels
    - Main heading exists and mentions Reels
    """
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to /generate/reels
            page.goto(f"{BASE}/generate/reels", wait_until="networkidle", timeout=10000)
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Check page title
            page_title = page.title()
            assert "Reels" in page_title or "Shorts" in page_title, "Page title should mention Reels or Shorts"
            
            # Check main heading
            main_heading = page.query_selector("#reels-heading")
            assert main_heading is not None, "Main heading should exist"
            
            heading_text = main_heading.inner_text()
            assert "Reels" in heading_text or "Shorts" in heading_text, "Main heading should mention Reels or Shorts"
            
            browser.close()
    
    finally:
        stop_server(proc)


def test_reels_page_has_quick_generate_button():
    """
    Test that /generate/reels has a quick generate button.
    
    Verifies:
    - Quick generate button exists
    - Button is visible and clickable
    """
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to /generate/reels
            page.goto(f"{BASE}/generate/reels", wait_until="networkidle", timeout=10000)
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Check for quick generate button
            quick_generate_btn = page.query_selector("#quick-generate-reel")
            assert quick_generate_btn is not None, "Quick generate button should exist"
            
            # Verify button is visible
            is_visible = quick_generate_btn.is_visible()
            assert is_visible, "Quick generate button should be visible"
            
            # Verify button has appropriate text
            button_text = quick_generate_btn.inner_text()
            assert "Generate" in button_text or "reel" in button_text.lower(), "Button should mention generating reels"
            
            browser.close()
    
    finally:
        stop_server(proc)
