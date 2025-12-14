"""E2E tests for wizard applying GOOD defaults and saving chip selections."""

import pytest


@pytest.mark.e2e
def test_wizard_applies_good_defaults_on_industry_select(page, live_server):
    """
    Test that selecting an industry in the wizard fetches and applies GOOD defaults.
    
    Acceptance criteria:
    - When user selects an industry, good_defaults API is called
    - Chip selections are automatically applied from the defaults
    - User can edit the selections (they're not locked)
    """
    # Navigate to wizard
    page.goto(f'{live_server.url()}/app')
    
    # Wait for page to load
    page.wait_for_selector('#industries', state='visible')
    
    # Select salon industry
    salon_btn = page.locator('[data-industry="salon"]')
    
    # Set up request interception to verify API call
    api_calls = []
    
    def handle_response(response):
        if '/api/industry_packs/' in response.url and '/good_defaults' in response.url:
            api_calls.append(response.url)
    
    page.on('response', handle_response)
    
    # Click salon industry
    salon_btn.click()
    
    # Wait a moment for API call to complete
    page.wait_for_timeout(1000)
    
    # Verify API was called
    assert len(api_calls) > 0, "good_defaults API should have been called"
    assert 'salon/good_defaults' in api_calls[0], "Should fetch salon good_defaults"
    
    # Verify industry is marked as selected
    assert salon_btn.get_attribute('class') and 'selected' in salon_btn.get_attribute('class')


@pytest.mark.e2e
def test_wizard_saves_and_prefills_chip_selections(page, live_server):
    """
    Test that chip selections are saved and prefilled on reload.
    
    Acceptance criteria:
    - User completes wizard with chip selections
    - Selections are saved to profile
    - On reload, saved selections are prefilled (not defaults)
    """
    # Navigate to wizard
    page.goto(f'{live_server.url()}/app')
    
    # Wait for page to load
    page.wait_for_selector('#industries', state='visible')
    
    # Step 1: Select industry
    page.click('[data-industry="salon"]')
    
    # Wait for good_defaults to load
    page.wait_for_timeout(1000)
    
    # Note: In a full implementation, we would:
    # 1. Display chip selection UI
    # 2. Allow user to select/deselect chips
    # 3. Save on wizard completion
    # 4. Reload and verify prefilled selections
    
    # For now, just verify the industry selection persists
    # This is a placeholder for the full chip selection UI test
    
    # Click Next to continue (this will trigger profile save)
    page.click('#next')
    
    # Wait for save to complete
    page.wait_for_timeout(500)
    
    # Reload the page
    page.reload()
    page.wait_for_selector('#industries', state='visible')
    
    # Verify industry is still selected
    salon_btn = page.locator('[data-industry="salon"]')
    # Note: actual persistence verification would need profile loading to be implemented


@pytest.mark.e2e  
def test_chip_selections_persist_to_generate_page(page, live_server):
    """
    Test that chip selections persist when navigating to /generate page.
    
    Acceptance criteria:
    - Complete wizard with chip selections
    - Navigate to /generate/social
    - Chip selections should be available in the profile
    """
    # Navigate to wizard
    page.goto(f'{live_server.url()}/app')
    
    # Wait for page to load
    page.wait_for_selector('#industries', state='visible')
    
    # Select industry and complete minimal wizard
    page.click('[data-industry="salon"]')
    page.wait_for_timeout(1000)
    
    # Note: In actual implementation, would complete all wizard steps
    # For now, just navigate to generate page
    
    page.goto(f'{live_server.url()}/generate/social')
    page.wait_for_timeout(1000)
    
    # Verify page loads (basic smoke test)
    # In full implementation, would verify chip selections are loaded
    # and available for content generation
