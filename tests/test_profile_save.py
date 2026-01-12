"""
Test suite for PROFILE-FIX-001: Profile Save Functionality

Validates that:
1. Profile save returns 2xx and persists fields reliably
2. Platforms and details arrays are preserved
3. Response structure includes proper fields
"""


def test_profile_save_success_persists_all_fields(client):
    """Profile POST returns 200 and persists company/industry/tone/platforms/details."""
    # Create a user first
    signup_response = client.post('/api/signup', json={
        'email': 'profilesave_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Save profile with all fields
    profile_data = {
        'company': 'Test Company',
        'industry': 'Software / Tech / Startup',
        'tone': 'professional',
        'platforms': ['instagram', 'linkedin', 'twitter'],
        'timezone': 'America/New_York',
        'brand_keywords': ['innovation', 'quality'],
        'goals': ['engagement', 'growth'],
        'target_audience': 'Tech professionals',
        'key_offer': 'Best software solutions',
        'voice_rules': 'No jargon, be clear'
    }
    
    save_response = client.post('/api/profile', json=profile_data)
    
    # Verify 200 response
    assert save_response.status_code == 200
    save_body = save_response.get_json()
    assert save_body.get('ok') is True
    assert save_body.get('request_id')
    assert save_body.get('message') == 'Profile saved successfully'
    
    # Verify persistence by fetching profile
    fetch_response = client.get('/api/profile')
    assert fetch_response.status_code == 200
    fetch_body = fetch_response.get_json()
    assert fetch_body.get('ok') is True
    
    profile = fetch_body.get('profile')
    assert profile is not None
    
    # Verify all fields persisted
    assert profile['company'] == 'Test Company'
    assert profile['industry'] == 'Software / Tech / Startup'
    assert profile['tone'] == 'professional'
    assert profile['platforms'] == ['instagram', 'linkedin', 'twitter']
    assert profile['timezone'] == 'America/New_York'
    assert profile['brand_keywords'] == ['innovation', 'quality']
    assert profile['goals'] == ['engagement', 'growth']
    assert profile['target_audience'] == 'Tech professionals'
    assert profile['key_offer'] == 'Best software solutions'
    assert profile['voice_rules'] == 'No jargon, be clear'


def test_profile_save_preserves_platforms_array(client):
    """Platforms array is properly preserved on save."""
    signup_response = client.post('/api/signup', json={
        'email': 'platforms_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Save with multiple platforms
    save_response = client.post('/api/profile', json={
        'company': 'Platform Test Co',
        'industry': 'Business',
        'tone': 'casual',
        'platforms': ['instagram', 'facebook', 'linkedin', 'tiktok']
    })
    assert save_response.status_code == 200
    
    # Fetch and verify
    fetch_response = client.get('/api/profile')
    profile = fetch_response.get_json()['profile']
    
    assert isinstance(profile['platforms'], list)
    assert len(profile['platforms']) == 4
    assert set(profile['platforms']) == {'instagram', 'facebook', 'linkedin', 'tiktok'}


def test_profile_save_preserves_empty_platforms(client):
    """Empty platforms array is preserved (API allows empty, UI may enforce constraints)."""
    signup_response = client.post('/api/signup', json={
        'email': 'empty_platforms_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Save with empty platforms
    save_response = client.post('/api/profile', json={
        'company': 'Empty Platform Co',
        'industry': 'Business',
        'tone': 'friendly',
        'platforms': []
    })
    # API allows empty arrays for flexibility
    assert save_response.status_code == 200
    
    # Fetch and verify empty list preserved
    fetch_response = client.get('/api/profile')
    profile = fetch_response.get_json()['profile']
    assert profile['platforms'] == []


def test_profile_save_preserves_details_arrays(client):
    """Arrays for keywords, goals, writing_samples are preserved."""
    signup_response = client.post('/api/signup', json={
        'email': 'arrays_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    details = {
        'company': 'Arrays Test Co',
        'industry': 'Business',
        'tone': 'professional',
        'brand_keywords': ['keyword1', 'keyword2', 'keyword3'],
        'goals': ['goal1', 'goal2'],
        'writing_samples': ['Sample 1 text here', 'Sample 2 text here'],
        'niche_keywords': ['niche1', 'niche2']
    }
    
    save_response = client.post('/api/profile', json=details)
    assert save_response.status_code == 200
    
    fetch_response = client.get('/api/profile')
    profile = fetch_response.get_json()['profile']
    
    assert profile['brand_keywords'] == ['keyword1', 'keyword2', 'keyword3']
    assert profile['goals'] == ['goal1', 'goal2']
    assert profile['writing_samples'] == ['Sample 1 text here', 'Sample 2 text here']
    assert profile['niche_keywords'] == ['niche1', 'niche2']


def test_profile_save_update_existing_profile(client):
    """Updating existing profile preserves ID and updates fields."""
    signup_response = client.post('/api/signup', json={
        'email': 'update_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # First save
    first_save_response = client.post('/api/profile', json={
        'company': 'Original Company',
        'industry': 'Business',
        'tone': 'formal',
        'platforms': ['instagram']
    })
    assert first_save_response.status_code == 200
    first_save_body = first_save_response.get_json()
    assert first_save_body.get('ok') is True
    
    # Get profile ID
    first_fetch = client.get('/api/profile')
    first_profile = first_fetch.get_json()['profile']
    original_id = first_profile['id']
    
    # Update profile
    update_response = client.post('/api/profile', json={
        'company': 'Updated Company',
        'industry': 'Tech',
        'tone': 'casual',
        'platforms': ['linkedin', 'twitter']
    })
    assert update_response.status_code == 200
    
    # Verify update
    second_fetch = client.get('/api/profile')
    second_profile = second_fetch.get_json()['profile']
    
    # Same ID (not creating new profile)
    assert second_profile['id'] == original_id
    
    # Fields updated
    assert second_profile['company'] == 'Updated Company'
    assert second_profile['industry'] == 'Tech'
    assert second_profile['tone'] == 'casual'
    assert second_profile['platforms'] == ['linkedin', 'twitter']


def test_profile_save_with_missing_optional_fields(client):
    """Profile can be saved with minimal data (optional fields omitted)."""
    signup_response = client.post('/api/signup', json={
        'email': 'minimal_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Save with minimal data
    minimal_data = {
        'company': 'Minimal Co',
        'industry': 'Business',
        'tone': 'neutral'
        # No platforms, keywords, goals, etc.
    }
    
    save_response = client.post('/api/profile', json=minimal_data)
    assert save_response.status_code == 200
    
    # Verify saved
    fetch_response = client.get('/api/profile')
    profile = fetch_response.get_json()['profile']
    
    assert profile['company'] == 'Minimal Co'
    assert profile['platforms'] == []  # Empty list for optional array fields
    assert profile['brand_keywords'] == []
    assert profile['goals'] == []


def test_profile_save_success_response_structure(client):
    """Response structure for successful save includes 'ok' and 'request_id' fields."""
    signup_response = client.post('/api/signup', json={
        'email': 'error_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Test successful save to verify response structure
    save_response = client.post('/api/profile', json={
        'company': 'Error Test Co',
        'industry': 'Business',
        'tone': 'test'
    })
    
    # Verify response has proper structure
    body = save_response.get_json()
    assert 'ok' in body
    assert body['ok'] is True
    assert 'request_id' in body
    
    # Note: Error responses (401/403/500) follow the same structure
    # with 'ok': False and 'error' object containing 'code' and 'message'


def test_profile_get_returns_empty_profile_for_new_user(client):
    """GET /api/profile returns empty profile (not 404) for new user."""
    signup_response = client.post('/api/signup', json={
        'email': 'newuser_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # Fetch profile before saving anything
    fetch_response = client.get('/api/profile')
    assert fetch_response.status_code == 200
    
    body = fetch_response.get_json()
    assert body.get('ok') is True
    assert body.get('profile_status') == 'empty'
    
    profile = body.get('profile')
    assert profile is not None
    assert profile['company'] == ''
    assert profile['industry'] == ''
    assert profile['tone'] == ''
    assert profile['platforms'] == []


def test_profile_save_returns_request_id(client):
    """All profile responses include request_id for tracing."""
    signup_response = client.post('/api/signup', json={
        'email': 'requestid_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # POST includes request_id
    save_response = client.post('/api/profile', json={
        'company': 'RequestID Co',
        'industry': 'Business',
        'tone': 'test'
    })
    save_body = save_response.get_json()
    assert 'request_id' in save_body
    assert save_body['request_id']  # Not empty
    
    # GET includes request_id
    fetch_response = client.get('/api/profile')
    fetch_body = fetch_response.get_json()
    assert 'request_id' in fetch_body
    assert fetch_body['request_id']  # Not empty
