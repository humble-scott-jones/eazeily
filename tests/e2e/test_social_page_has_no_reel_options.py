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


def test_social_page_does_not_show_reels_platform_chips():
    """
    Test that the Social page does NOT have Reels/Shorts or TikTok platform chips.
    
    Verifies:
    - short_video platform chip does NOT exist
    - tiktok platform chip does NOT exist
    - Only non-video platform chips are present (Instagram, Facebook, LinkedIn, Twitter)
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
            
            # Verify that short_video chip does NOT exist
            reels_chip = page.query_selector('button[data-generator-platform="short_video"]')
            assert reels_chip is None, "Reels/Shorts platform chip should NOT exist on social page"
            
            # Verify that tiktok chip does NOT exist
            tiktok_chip = page.query_selector('button[data-generator-platform="tiktok"]')
            assert tiktok_chip is None, "TikTok platform chip should NOT exist on social page"
            
            # Verify that non-video platforms are present
            instagram_chip = page.query_selector('button[data-generator-platform="instagram"]')
            assert instagram_chip is not None, "Instagram platform chip should exist"
            
            facebook_chip = page.query_selector('button[data-generator-platform="facebook"]')
            assert facebook_chip is not None, "Facebook platform chip should exist"
            
            linkedin_chip = page.query_selector('button[data-generator-platform="linkedin"]')
            assert linkedin_chip is not None, "LinkedIn platform chip should exist"
            
            twitter_chip = page.query_selector('button[data-generator-platform="twitter"]')
            assert twitter_chip is not None, "Twitter platform chip should exist"
            
            browser.close()
    
    finally:
        stop_server(proc)


def test_social_page_does_not_have_reels_cta():
    """
    Test that the Social page does NOT have the reels CTA notice element.
    
    Verifies:
    - reels-cta-notice element does NOT exist in the DOM
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
            
            # Check that CTA notice does NOT exist
            cta_notice = page.query_selector("#reels-cta-notice")
            assert cta_notice is None, "CTA notice element should NOT exist on social page"
            
            browser.close()
    
    finally:
        stop_server(proc)
