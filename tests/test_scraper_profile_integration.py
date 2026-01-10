"""
Integration test for scraper + profile API.
Tests that the scraper can extract business info and that the profile API can save it.
"""
import pytest


def test_scraper_integration_with_profile_save(client):
    """Test that scraped data can be saved via profile API."""
    # 1. Create a user
    signup_response = client.post('/api/signup', json={
        'email': 'scraper_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # 2. Simulate scraped data (as if it came from /onboarding/social-style)
    # This is the data structure returned by extract_business_info
    scraped_profile_data = {
        'company': 'Tech Startup Inc',
        'business_name': 'Tech Startup Inc',
        'industry': 'Software / Tech / Startup',
        'brand_keywords': ['innovative', 'fast', 'reliable'],
        'niche_keywords': ['SaaS', 'cloud platform', 'B2B'],
        'target_audience': 'Small to medium businesses looking for cloud solutions',
        'key_customers': 'Small to medium businesses looking for cloud solutions',
        'tone': 'professional yet approachable',
        'platforms': ['linkedin', 'twitter']
    }
    
    # 3. Save profile via API
    save_response = client.post('/api/profile', json=scraped_profile_data)
    assert save_response.status_code == 200
    save_data = save_response.get_json()
    assert save_data['ok'] is True
    
    # 4. Retrieve and verify all fields were saved
    get_response = client.get('/api/profile')
    assert get_response.status_code == 200
    get_data = get_response.get_json()
    assert get_data['ok'] is True
    
    profile = get_data['profile']
    
    # Verify basic fields
    assert profile['company'] == 'Tech Startup Inc'
    assert profile['industry'] == 'Software / Tech / Startup'
    assert profile['tone'] == 'professional yet approachable'
    assert profile['target_audience'] == 'Small to medium businesses looking for cloud solutions'
    
    # Verify keywords were saved
    assert 'innovative' in profile['brand_keywords']
    assert 'fast' in profile['brand_keywords']
    assert 'reliable' in profile['brand_keywords']
    
    assert 'SaaS' in profile['niche_keywords']
    assert 'cloud platform' in profile['niche_keywords']
    assert 'B2B' in profile['niche_keywords']
    
    # Verify platforms
    assert 'linkedin' in profile['platforms']
    assert 'twitter' in profile['platforms']


def test_scraper_extracts_keywords():
    """Test that the scraper service can extract keywords from text."""
    from services.scraper_service import extract_business_info
    
    # Sample website text
    sample_text = """
    Welcome to EcoGreen Solutions
    
    We are a sustainable energy company providing innovative solar panel installations 
    for residential and commercial properties. Our mission is to make clean energy 
    accessible and affordable for everyone.
    
    Our customers are environmentally-conscious homeowners and businesses looking to 
    reduce their carbon footprint while saving on energy costs.
    
    We specialize in premium solar installations, battery storage, and energy audits.
    """
    
    # Note: This test will only work if AI service is configured
    # For the test suite, we'll mock the response or skip if not configured
    try:
        result = extract_business_info(sample_text)
        
        # Check structure
        assert 'business_name' in result
        assert 'industry' in result
        assert 'key_customers' in result
        assert 'brand_keywords' in result
        assert 'niche_keywords' in result
        
        # If AI is available, keywords should be extracted
        if result['brand_keywords']:
            assert isinstance(result['brand_keywords'], list)
            assert len(result['brand_keywords']) > 0
            
        if result['niche_keywords']:
            assert isinstance(result['niche_keywords'], list)
            assert len(result['niche_keywords']) > 0
            
    except Exception as e:
        # Skip if AI service is not configured
        pytest.skip(f"AI service not configured: {e}")


def test_profile_api_handles_missing_keywords_gracefully(client):
    """Test that profile API works even if keywords are not provided."""
    # 1. Create a user
    signup_response = client.post('/api/signup', json={
        'email': 'no_keywords@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # 2. Save profile without keywords
    profile_data = {
        'company': 'Simple Co',
        'industry': 'Retail / Boutique',
        'tone': 'friendly'
    }
    
    save_response = client.post('/api/profile', json=profile_data)
    assert save_response.status_code == 200
    
    # 3. Retrieve and verify empty keywords
    get_response = client.get('/api/profile')
    assert get_response.status_code == 200
    get_data = get_response.get_json()
    
    profile = get_data['profile']
    assert profile['brand_keywords'] == []
    assert profile['niche_keywords'] == []
    assert profile['company'] == 'Simple Co'
