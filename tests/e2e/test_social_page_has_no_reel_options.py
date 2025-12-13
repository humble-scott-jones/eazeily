"""
E2E test to verify that /generate/social does NOT render "Reel Options"
and shows a CTA linking to /generate/reels when Reels/TikTok platform is selected.

Tests acceptance criteria:
- /generate/social does not render "Reel Options" anywhere
- Selecting Reels/TikTok in Social shows a CTA linking to the Reels tab
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


def test_social_page_has_no_reel_options():
    """
    Test that /generate/social does NOT render "Reel Options" section.
    
    Verifies:
    - Page loads successfully
    - "Reel Options" text is NOT present anywhere on the page
    - No element with id "reel-options" exists
    """
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to /generate/social
            page.goto(f"{BASE}/generate/social", wait_until="networkidle", timeout=10000)
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Check that "Reel Options" text is NOT present
            page_content = page.content()
            assert "Reel Options" not in page_content, "Page should not contain 'Reel Options' text"
            
            # Check that the old reel-options element does NOT exist
            reel_options_el = page.query_selector("#reel-options")
            assert reel_options_el is None, "Element #reel-options should not exist on social page"
            
            browser.close()
    
    finally:
        stop_server(proc)


def test_social_page_shows_reels_cta_on_platform_select():
    """
    Test that selecting Reels/TikTok platform shows a CTA linking to /generate/reels.
    
    Verifies:
    - CTA notice appears when Reels/Shorts platform is selected
    - CTA contains link to /generate/reels
    - CTA text mentions "Reels tab"
    """
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to /generate/social
            page.goto(f"{BASE}/generate/social", wait_until="networkidle", timeout=10000)
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Find and click the "Reels / Shorts" platform chip
            reels_chip = page.query_selector('button[data-generator-platform="short_video"]')
            assert reels_chip is not None, "Reels/Shorts platform chip should exist"
            
            # Click the chip to select it
            reels_chip.click()
            
            # Wait for UI to update
            time.sleep(1)
            
            # Check that CTA notice appears
            cta_notice = page.query_selector("#reels-cta-notice")
            assert cta_notice is not None, "CTA notice should exist"
            
            # Check that CTA is visible (not hidden)
            is_hidden = cta_notice.evaluate("el => el.classList.contains('hidden')")
            assert not is_hidden, "CTA notice should be visible when Reels platform is selected"
            
            # Check that CTA contains text about Reels tab
            cta_text = cta_notice.inner_text()
            assert "Reels tab" in cta_text or "Reels" in cta_text, "CTA should mention Reels"
            
            # Check that CTA contains link to /generate/reels
            reels_link = cta_notice.query_selector('a[href="/generate/reels"]')
            assert reels_link is not None, "CTA should contain link to /generate/reels"
            
            browser.close()
    
    finally:
        stop_server(proc)


def test_tiktok_platform_also_shows_cta():
    """
    Test that selecting TikTok platform also shows the CTA.
    
    Verifies:
    - CTA notice appears when TikTok platform is selected
    """
    proc = start_server()
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            # Navigate to /generate/social
            page.goto(f"{BASE}/generate/social", wait_until="networkidle", timeout=10000)
            
            # Wait for page to fully load
            time.sleep(2)
            
            # Find and click the TikTok platform chip
            tiktok_chip = page.query_selector('button[data-generator-platform="tiktok"]')
            assert tiktok_chip is not None, "TikTok platform chip should exist"
            
            # Click the chip to select it
            tiktok_chip.click()
            
            # Wait for UI to update
            time.sleep(1)
            
            # Check that CTA notice is visible
            cta_notice = page.query_selector("#reels-cta-notice")
            assert cta_notice is not None, "CTA notice should exist"
            
            is_hidden = cta_notice.evaluate("el => el.classList.contains('hidden')")
            assert not is_hidden, "CTA notice should be visible when TikTok platform is selected"
            
            browser.close()
    
    finally:
        stop_server(proc)
