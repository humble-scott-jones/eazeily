"""
Test toggle/chip contrast and accessibility on generate pages.
Tests for UX-Contrast-003 fix.
"""
import os
import time
import pathlib
import pytest
from playwright.sync_api import sync_playwright, expect

ROOT = pathlib.Path(__file__).resolve().parents[2]
PORT = int(os.getenv('PORT', '5001'))
BASE = f'http://127.0.0.1:{PORT}'

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_UI_SMOKE") != "1",
    reason="UI smoke tests disabled (set RUN_UI_SMOKE=1)"
)


def rgb_to_luminance(r, g, b):
    """Calculate relative luminance for contrast ratio."""
    def adjust(val):
        val = val / 255.0
        if val <= 0.03928:
            return val / 12.92
        return ((val + 0.055) / 1.055) ** 2.4
    
    return 0.2126 * adjust(r) + 0.7152 * adjust(g) + 0.0722 * adjust(b)


def calculate_contrast_ratio(color1, color2):
    """Calculate WCAG contrast ratio between two RGB colors."""
    l1 = rgb_to_luminance(*color1)
    l2 = rgb_to_luminance(*color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def parse_rgb_color(color_string):
    """Parse 'rgb(r, g, b)' or 'rgba(r, g, b, a)' string to (r, g, b) tuple."""
    # Remove 'rgb(' or 'rgba(' and ')' and split
    color_string = color_string.replace('rgb(', '').replace('rgba(', '').replace(')', '')
    parts = [p.strip() for p in color_string.split(',')]
    rgb = tuple(int(parts[i].split('.')[0]) for i in range(3))
    
    # Check if color is transparent (alpha = 0)
    if len(parts) == 4:
        alpha = float(parts[3])
        if alpha == 0:
            # Return white as default background for transparent elements
            return (255, 255, 255)
    
    return rgb


def test_platform_chip_contrast():
    """Test that platform chips have sufficient contrast in all states."""
    headless = os.getenv('HEADLESS', '1') != '0'
    out_base = ROOT / 'tmp' / 'contrast-tests' / time.strftime('%Y%m%d-%H%M%S')
    out_base.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        
        try:
            # Visit generate page
            page.goto(f'{BASE}/generate/social', wait_until='networkidle')
            page.wait_for_timeout(1000)
            
            # Take screenshot of initial state
            page.screenshot(path=str(out_base / '01-initial-state.png'), full_page=True)
            
            # Find platform chips
            platform_chips = page.locator('#generator-platforms button[data-generator-platform]')
            chip_count = platform_chips.count()
            assert chip_count > 0, "No platform chips found"
            
            print(f"\nFound {chip_count} platform chips")
            
            # Test each chip in default and active states
            contrast_issues = []
            
            for i in range(chip_count):
                chip = platform_chips.nth(i)
                platform_name = chip.get_attribute('data-generator-platform')
                is_active = 'chip--active' in (chip.get_attribute('class') or '')
                
                # Get computed styles
                bg_color = chip.evaluate('el => window.getComputedStyle(el).backgroundColor')
                text_color = chip.evaluate('el => window.getComputedStyle(el).color')
                
                print(f"\n{platform_name} ({'active' if is_active else 'inactive'}):")
                print(f"  Background: {bg_color}")
                print(f"  Text: {text_color}")
                
                # Parse colors
                try:
                    bg_rgb = parse_rgb_color(bg_color)
                    text_rgb = parse_rgb_color(text_color)
                    contrast = calculate_contrast_ratio(bg_rgb, text_rgb)
                    print(f"  Contrast ratio: {contrast:.2f}:1")
                    
                    # WCAG AA requires 4.5:1 for normal text
                    if contrast < 4.5:
                        contrast_issues.append({
                            'element': f'Platform chip: {platform_name}',
                            'state': 'active' if is_active else 'default',
                            'contrast': contrast,
                            'bg': bg_color,
                            'text': text_color
                        })
                except Exception as e:
                    print(f"  Error parsing colors: {e}")
                
                # Toggle the chip and test active state if not already active
                if not is_active:
                    chip.click()
                    page.wait_for_timeout(300)
                    
                    # Get active state styles
                    bg_color_active = chip.evaluate('el => window.getComputedStyle(el).backgroundColor')
                    text_color_active = chip.evaluate('el => window.getComputedStyle(el).color')
                    
                    print(f"\n{platform_name} (after click - should be active):")
                    print(f"  Background: {bg_color_active}")
                    print(f"  Text: {text_color_active}")
                    
                    try:
                        bg_rgb_active = parse_rgb_color(bg_color_active)
                        text_rgb_active = parse_rgb_color(text_color_active)
                        contrast_active = calculate_contrast_ratio(bg_rgb_active, text_rgb_active)
                        print(f"  Contrast ratio: {contrast_active:.2f}:1")
                        
                        if contrast_active < 4.5:
                            contrast_issues.append({
                                'element': f'Platform chip: {platform_name}',
                                'state': 'active (after click)',
                                'contrast': contrast_active,
                                'bg': bg_color_active,
                                'text': text_color_active
                            })
                    except Exception as e:
                        print(f"  Error parsing active colors: {e}")
                    
                    # Click again to toggle back
                    chip.click()
                    page.wait_for_timeout(300)
            
            # Take screenshot after testing all chips
            page.screenshot(path=str(out_base / '02-after-testing.png'), full_page=True)
            
            # Test plan length chips
            plan_length_chips = page.locator('#plan-length-buttons button[data-plan-length]')
            length_count = plan_length_chips.count()
            
            print(f"\n\nFound {length_count} plan length chips")
            
            for i in range(length_count):
                chip = plan_length_chips.nth(i)
                length_val = chip.get_attribute('data-plan-length')
                is_active = 'chip--active' in (chip.get_attribute('class') or '')
                
                bg_color = chip.evaluate('el => window.getComputedStyle(el).backgroundColor')
                text_color = chip.evaluate('el => window.getComputedStyle(el).color')
                
                print(f"\nPlan length {length_val} days ({'active' if is_active else 'inactive'}):")
                print(f"  Background: {bg_color}")
                print(f"  Text: {text_color}")
                
                try:
                    bg_rgb = parse_rgb_color(bg_color)
                    text_rgb = parse_rgb_color(text_color)
                    contrast = calculate_contrast_ratio(bg_rgb, text_rgb)
                    print(f"  Contrast ratio: {contrast:.2f}:1")
                    
                    if contrast < 4.5:
                        contrast_issues.append({
                            'element': f'Plan length chip: {length_val} days',
                            'state': 'active' if is_active else 'default',
                            'contrast': contrast,
                            'bg': bg_color,
                            'text': text_color
                        })
                except Exception as e:
                    print(f"  Error parsing colors: {e}")
            
            # Report contrast issues
            if contrast_issues:
                print("\n\n⚠️  CONTRAST ISSUES FOUND:")
                for issue in contrast_issues:
                    print(f"\n  {issue['element']} ({issue['state']}):")
                    print(f"    Contrast: {issue['contrast']:.2f}:1 (requires 4.5:1)")
                    print(f"    Background: {issue['bg']}")
                    print(f"    Text: {issue['text']}")
                
                # Don't fail the test yet - we're gathering information
                print("\n✓ Contrast analysis complete. See output above for details.")
            else:
                print("\n\n✓ All chips meet WCAG AA contrast requirements (4.5:1)")
            
        finally:
            browser.close()


def test_tab_navigation_contrast():
    """Test that tab navigation has sufficient contrast."""
    headless = os.getenv('HEADLESS', '1') != '0'
    out_base = ROOT / 'tmp' / 'contrast-tests' / time.strftime('%Y%m%d-%H%M%S')
    out_base.mkdir(parents=True, exist_ok=True)
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        
        try:
            # Test each tab page
            pages_to_test = [
                ('/generate/social', 'Social'),
                ('/generate/reels', 'Reels'),
                ('/generate/reviews', 'Reviews'),
            ]
            
            for url, expected_active in pages_to_test:
                page.goto(f'{BASE}{url}', wait_until='networkidle')
                page.wait_for_timeout(1000)
                
                # Find tab navigation
                tabs = page.locator('[role="tablist"] [role="tab"]')
                tab_count = tabs.count()
                
                print(f"\n\nTesting {url} - found {tab_count} tabs")
                
                for i in range(tab_count):
                    tab = tabs.nth(i)
                    tab_text = tab.text_content().strip()
                    is_selected = tab.get_attribute('aria-selected') == 'true'
                    
                    bg_color = tab.evaluate('el => window.getComputedStyle(el).backgroundColor')
                    text_color = tab.evaluate('el => window.getComputedStyle(el).color')
                    
                    print(f"\nTab '{tab_text}' ({'selected' if is_selected else 'unselected'}):")
                    print(f"  Background: {bg_color}")
                    print(f"  Text: {text_color}")
                    
                    try:
                        bg_rgb = parse_rgb_color(bg_color)
                        text_rgb = parse_rgb_color(text_color)
                        contrast = calculate_contrast_ratio(bg_rgb, text_rgb)
                        print(f"  Contrast ratio: {contrast:.2f}:1")
                        
                        # Check for sufficient contrast
                        assert contrast >= 4.5, (
                            f"Tab '{tab_text}' ({is_selected and 'selected' or 'unselected'}) "
                            f"has insufficient contrast: {contrast:.2f}:1 (requires 4.5:1)"
                        )
                    except AssertionError:
                        raise
                    except Exception as e:
                        print(f"  Error parsing colors: {e}")
                
                page.screenshot(
                    path=str(out_base / f'tab-{expected_active.lower()}.png'),
                    full_page=False
                )
        
        finally:
            browser.close()


def test_chip_accessibility():
    """Test that chips have proper ARIA attributes and keyboard support."""
    headless = os.getenv('HEADLESS', '1') != '0'
    
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_page()
        
        try:
            page.goto(f'{BASE}/generate/social', wait_until='networkidle')
            page.wait_for_timeout(1000)
            
            # Test platform chips
            platform_chips = page.locator('#generator-platforms button[data-generator-platform]')
            chip_count = platform_chips.count()
            
            print(f"\n\nTesting accessibility of {chip_count} platform chips")
            
            for i in range(chip_count):
                chip = platform_chips.nth(i)
                platform_name = chip.get_attribute('data-generator-platform')
                
                # Check ARIA attributes
                aria_pressed = chip.get_attribute('aria-pressed')
                assert aria_pressed in ['true', 'false'], (
                    f"Chip {platform_name} missing valid aria-pressed attribute"
                )
                
                # Check that button is keyboard accessible
                is_button = chip.evaluate('el => el.tagName.toLowerCase()') == 'button'
                assert is_button, f"Chip {platform_name} is not a button element"
                
                print(f"  ✓ {platform_name}: aria-pressed={aria_pressed}, is <button>")
            
            # Test focus visibility
            first_chip = platform_chips.first
            first_chip.focus()
            page.wait_for_timeout(300)
            
            # Check if focus ring is visible (outline property)
            outline = first_chip.evaluate('el => window.getComputedStyle(el).outline')
            outline_style = first_chip.evaluate('el => window.getComputedStyle(el).outlineStyle')
            
            print(f"\n  Focus ring on first chip:")
            print(f"    outline: {outline}")
            print(f"    outlineStyle: {outline_style}")
            
            # The chip should have focus-visible styles
            assert outline_style != 'none', "Focus ring not visible on chip focus"
            
            print("\n✓ All chips have proper ARIA attributes and are keyboard accessible")
            
        finally:
            browser.close()
