import pytest


def test_profile_page_requires_login(client):
    """Test that /profile requires authentication."""
    response = client.get('/profile', follow_redirects=False)
    assert response.status_code in (302, 401)  # Redirect to login or unauthorized


def test_profile_page_loads_for_authenticated_user(client):
    """Test that authenticated users can access /profile."""
    # Create and login a user
    signup_response = client.post('/api/signup', json={
        'email': 'profiletest@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Access profile page
    response = client.get('/profile')
    assert response.status_code == 200
    assert b'Brand Profile' in response.data or b'profile' in response.data.lower()


def test_profile_page_save_flow(client):
    """Test the complete profile save flow from the new profile page."""
    # Create and login a user
    signup_response = client.post('/api/signup', json={
        'email': 'profilesave@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Create a profile via API
    profile_data = {
        'company': 'Test Company',
        'industry': 'software',
        'tone': 'Professional',
        'platforms': ['instagram', 'linkedin'],
        'brand_keywords': ['innovative', 'reliable'],
        'goals': ['engagement', 'growth']
    }
    
    save_response = client.post('/api/profile', json=profile_data)
    assert save_response.status_code == 200
    data = save_response.get_json()
    assert data.get('ok') is True
    
    # Verify profile was saved
    get_response = client.get('/api/profile')
    assert get_response.status_code == 200
    get_data = get_response.get_json()
    assert get_data.get('ok') is True
    profile = get_data.get('profile')
    assert profile['company'] == 'Test Company'
    assert profile['industry'] == 'software'
    assert profile['tone'] == 'Professional'
    assert 'instagram' in profile['platforms']
    assert 'linkedin' in profile['platforms']
    
    # Update profile
    updated_profile_data = {
        'company': 'Updated Company',
        'industry': 'healthcare',
        'tone': 'Friendly',
        'platforms': ['facebook', 'twitter'],
    }
    
    update_response = client.post('/api/profile', json=updated_profile_data)
    assert update_response.status_code == 200
    
    # Verify update
    verify_response = client.get('/api/profile')
    verify_data = verify_response.get_json()
    updated_profile = verify_data.get('profile')
    assert updated_profile['company'] == 'Updated Company'
    assert updated_profile['industry'] == 'healthcare'
    assert updated_profile['tone'] == 'Friendly'


def test_profile_preserves_complex_fields(client):
    """Test that profile correctly handles arrays and complex fields."""
    # Create and login
    signup_response = client.post('/api/signup', json={
        'email': 'complexprofile@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Save profile with complex fields
    profile_data = {
        'company': 'Complex Co',
        'industry': 'software',
        'tone': 'Professional',
        'platforms': ['instagram', 'linkedin', 'twitter'],
        'brand_keywords': ['innovative', 'reliable', 'trusted'],
        'goals': ['engagement', 'growth', 'leads'],
        'target_audience': 'Small business owners aged 30-50',
        'key_offer': 'Streamlined business management tools',
        'voice_rules': 'Always use inclusive language, avoid jargon',
        'writing_samples': ['Sample 1', 'Sample 2', 'Sample 3']
    }
    
    save_response = client.post('/api/profile', json=profile_data)
    assert save_response.status_code == 200
    
    # Verify all fields
    get_response = client.get('/api/profile')
    get_data = get_response.get_json()
    profile = get_data.get('profile')
    
    assert len(profile['platforms']) == 3
    assert len(profile['brand_keywords']) == 3
    assert len(profile['goals']) == 3
    assert len(profile['writing_samples']) == 3
    assert profile['target_audience'] == 'Small business owners aged 30-50'
    assert profile['key_offer'] == 'Streamlined business management tools'
    assert profile['voice_rules'] == 'Always use inclusive language, avoid jargon'
