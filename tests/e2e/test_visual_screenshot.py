"""
Visual screenshot test to document the contrast fixes.
"""
import os
import time
import pathlib
import pytest
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv('PORT', '5001'))
BASE = f'http://127.0.0.1:{PORT}'

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_UI_SMOKE") != "1",
    reason="UI smoke tests disabled (set RUN_UI_SMOKE=1)"
)


def test_screenshot_generate_pages():
    """Take screenshots of all generate pages showing the fixed toggles."""
    headless = os.getenv('HEADLESS', '1') != '0'
    out_base = ROOT / 'tmp' / 'screenshots' / time.strftime('%Y%m%d-%H%M%S')
    out_base.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as pw:
        # Use a larger viewport to show more content
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(viewport={'width': 1400, 'height': 1000})
        page = context.new_page()
        
        try:
            # Screenshot Social page
            page.goto(f'{BASE}/generate/social', wait_until='networkidle')
            page.wait_for_timeout(1000)
            
            # Scroll to show the platform chips
            page.evaluate('window.scrollTo(0, 200)')
            page.wait_for_timeout(500)
            
            page.screenshot(
                path=str(out_base / 'generate-social-full.png'),
                full_page=False
            )
            
            # Take a focused screenshot of just the chips section
            chips_section = page.locator('#content-generator')
            if chips_section.count() > 0:
                chips_section.screenshot(path=str(out_base / 'platform-chips-section.png'))
            
            # Click a few chips to show active state
            page.locator('button[data-generator-platform="facebook"]').click()
            page.wait_for_timeout(300)
            page.locator('button[data-generator-platform="linkedin"]').click()
            page.wait_for_timeout(300)
            
            # Screenshot with multiple active chips
            if chips_section.count() > 0:
                chips_section.screenshot(path=str(out_base / 'platform-chips-active.png'))
            
            # Screenshot tab navigation
            page.goto(f'{BASE}/generate/social', wait_until='networkidle')
            page.wait_for_timeout(1000)
            
            tabs = page.locator('[role="tablist"]')
            if tabs.count() > 0:
                tabs.screenshot(path=str(out_base / 'tab-navigation-social.png'))
            
            # Screenshot Reels tab
            page.goto(f'{BASE}/generate/reels', wait_until='networkidle')
            page.wait_for_timeout(1000)
            
            if tabs.count() > 0:
                tabs.screenshot(path=str(out_base / 'tab-navigation-reels.png'))
            
            page.screenshot(
                path=str(out_base / 'generate-reels-full.png'),
                full_page=False
            )
            
            # Screenshot Reviews page
            page.goto(f'{BASE}/generate/reviews', wait_until='networkidle')
            page.wait_for_timeout(1000)
            
            if tabs.count() > 0:
                tabs.screenshot(path=str(out_base / 'tab-navigation-reviews.png'))
            
            # Screenshot the review length chips
            length_options = page.locator('#length-options')
            if length_options.count() > 0:
                length_options.screenshot(path=str(out_base / 'review-length-chips.png'))
            
            page.screenshot(
                path=str(out_base / 'generate-reviews-full.png'),
                full_page=False
            )
            
            print(f"\n✓ Screenshots saved to: {out_base}")
            print(f"  - generate-social-full.png")
            print(f"  - platform-chips-section.png")
            print(f"  - platform-chips-active.png")
            print(f"  - tab-navigation-*.png")
            print(f"  - generate-reels-full.png")
            print(f"  - generate-reviews-full.png")
            print(f"  - review-length-chips.png")
            
        finally:
            browser.close()
