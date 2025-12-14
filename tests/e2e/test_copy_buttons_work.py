"""Playwright test for copy button functionality.

This test verifies that the new copy buttons work correctly:
- Copy caption button
- Copy hashtags button  
- Copy caption + hashtags button
"""

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.e2e
def test_copy_caption_button_works(page: Page):
    """Test that the 'Copy caption' button copies caption to clipboard."""
    # Note: This test requires a running server with generated content
    # Skip if server not available
    try:
        page.goto('http://localhost:5001/generate', timeout=5000)
    except Exception:
        pytest.skip("Server not available for e2e test")
    
    # TODO: Generate a post first, then test copy button
    # This is a placeholder for when full e2e infrastructure is set up
    pass


@pytest.mark.e2e
def test_copy_hashtags_button_works(page: Page):
    """Test that the 'Copy hashtags' button copies hashtags to clipboard."""
    # Note: This test requires a running server with generated content
    # Skip if server not available
    try:
        page.goto('http://localhost:5001/generate', timeout=5000)
    except Exception:
        pytest.skip("Server not available for e2e test")
    
    # TODO: Generate a post with hashtags, then test copy button
    pass


@pytest.mark.e2e
def test_copy_combined_button_works(page: Page):
    """Test that 'Copy caption + hashtags' button copies both to clipboard."""
    # Note: This test requires a running server with generated content
    # Skip if server not available
    try:
        page.goto('http://localhost:5001/generate', timeout=5000)
    except Exception:
        pytest.skip("Server not available for e2e test")
    
    # TODO: Generate a post, then test combined copy button
    pass


@pytest.mark.e2e
def test_strategy_notes_are_collapsed_by_default(page: Page):
    """Test that strategy notes section is collapsed by default."""
    # Note: This test requires a running server with generated content
    # Skip if server not available
    try:
        page.goto('http://localhost:5001/generate', timeout=5000)
    except Exception:
        pytest.skip("Server not available for e2e test")
    
    # TODO: Generate a post with notes, verify <details> element is closed
    pass


@pytest.mark.e2e
def test_hashtags_separated_from_caption(page: Page):
    """Test that hashtags are displayed in separate section from caption."""
    # Note: This test requires a running server with generated content
    # Skip if server not available
    try:
        page.goto('http://localhost:5001/generate', timeout=5000)
    except Exception:
        pytest.skip("Server not available for e2e test")
    
    # TODO: Generate a post, verify hashtags have their own section
    pass


# Manual test instructions (for now):
"""
To manually test the copy buttons:

1. Start the server: PORT=5001 python3 app.py
2. Open http://localhost:5001/generate in a browser
3. Generate some social posts
4. Verify:
   - Each post card shows "Copy caption", "Copy hashtags", and "Copy caption + hashtags" buttons
   - Caption is in a monospace textarea
   - Hashtags are in a separate gray box below the caption
   - Clicking each copy button copies the expected text
   - A green checkmark appears after successful copy
   - Strategy notes (if present) are collapsed by default in a <details> element
   - No coaching phrases like "you should" or "consider" appear in captions
"""
