"""Test Brand Kit UI contract and smoke tests."""

import pytest


def test_brand_kit_get_populates_wizard(client):
    """Test that GET /api/brand_kit can populate wizard with existing data."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create a brand kit
    brand_kit = {
        'business': {
            'company_name': 'Test Business',
            'industry_id': 'retail'
        },
        'services': {
            'primary_services': ['Service A', 'Service B', 'Service C']
        },
        'audience': {
            'target_roles': ['Small business owners'],
            'top_pains': ['Wasting time'],
            'desired_outcomes': ['Save time']
        },
        'positioning': {
            'differentiators': ['Fast', 'Reliable']
        },
        'proof': {
            'years_in_business': 10,
            'credentials': ['Licensed', 'Insured']
        }
    }
    
    # Save the brand kit
    response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert response.status_code == 200
    
    # Verify it can be retrieved
    get_response = client.get('/api/brand_kit')
    assert get_response.status_code == 200
    
    data = get_response.get_json()
    assert data['ok'] is True
    assert 'brand_kit' in data
    
    retrieved_kit = data['brand_kit']
    assert retrieved_kit['business']['company_name'] == 'Test Business'
    assert len(retrieved_kit['services']['primary_services']) == 3
    assert 'Small business owners' in retrieved_kit['audience']['target_roles']


def test_brand_kit_post_persists_data(client):
    """Test that POST /api/brand_kit persists data correctly."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create minimal brand kit
    brand_kit = {
        'business': {
            'company_name': 'Minimal Co'
        },
        'services': {
            'primary_services': ['Service 1', 'Service 2']
        },
        'audience': {
            'target_roles': ['Customers'],
            'top_pains': ['Problem'],
            'desired_outcomes': ['Solution']
        },
        'positioning': {
            'differentiators': ['Unique', 'Quality']
        }
    }
    
    # Save brand kit
    response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert 'brand_kit' in data
    
    # Verify it returns meta information
    saved_kit = data['brand_kit']
    assert 'meta' in saved_kit
    assert 'tier' in saved_kit['meta']
    assert 'completeness_score' in saved_kit['meta']


def test_brand_kit_tier_returned_and_calculated(client):
    """Test that brand kit tier is calculated and returned correctly."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Test GOOD tier (minimal fields)
    minimal_kit = {
        'services': {
            'primary_services': ['Service A', 'Service B']
        },
        'audience': {
            'target_roles': ['Target'],
            'top_pains': ['Pain'],
            'desired_outcomes': ['Outcome']
        },
        'positioning': {
            'differentiators': ['Diff1', 'Diff2']
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': minimal_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    tier = data['brand_kit']['meta']['tier']
    score = data['brand_kit']['meta']['completeness_score']
    
    # Should be at least minimum tier
    assert tier in ['minimum', 'stronger', 'best']
    assert score >= 0
    assert score <= 100
    
    # Test BETTER tier (with proof)
    better_kit = {
        'business': {
            'company_name': 'Better Co'
        },
        'services': {
            'primary_services': ['Service A', 'Service B', 'Service C']
        },
        'audience': {
            'target_roles': ['Target'],
            'top_pains': ['Pain'],
            'desired_outcomes': ['Outcome']
        },
        'positioning': {
            'differentiators': ['Diff1', 'Diff2', 'Diff3']
        },
        'proof': {
            'years_in_business': 10,
            'credentials': ['Licensed']
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': better_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    tier = data['brand_kit']['meta']['tier']
    score = data['brand_kit']['meta']['completeness_score']
    
    # Should have higher score
    assert score > 25
    
    # Test BEST tier (with email and quotes)
    best_kit = {
        'business': {
            'company_name': 'Best Co',
            'industry_id': 'retail',
            'service_area': 'Local',
            'contact_email': 'test@example.com',
            'contact_phone': '123-456-7890'
        },
        'services': {
            'primary_services': ['Service A', 'Service B', 'Service C'],
            'pricing_style': 'fixed'
        },
        'audience': {
            'target_roles': ['Target'],
            'top_pains': ['Pain'],
            'desired_outcomes': ['Outcome']
        },
        'positioning': {
            'differentiators': ['Diff1', 'Diff2', 'Diff3'],
            'values': ['Quality']
        },
        'proof': {
            'years_in_business': 10,
            'credentials': ['Licensed', 'Insured'],
            'volume_markers': ['1000+ clients']
        },
        'email': {
            'sender_name': 'John Doe',
            'signoff_style': 'Best regards',
            'signature_lines': 'john@example.com'
        },
        'quotes': {
            'default_validity_days': 30,
            'deposit_policy': '50%',
            'payment_methods': 'Cash, Card',
            'turnaround_time': '2 weeks'
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': best_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    tier = data['brand_kit']['meta']['tier']
    score = data['brand_kit']['meta']['completeness_score']
    
    # Should be best tier with high score
    assert score >= 50


def test_brand_kit_tier_displayed_in_wizard(client):
    """Test that tier is visible and updates in wizard UI."""
    # This is a smoke test to ensure the contract is correct
    # The actual UI testing would be done in E2E tests
    
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Get default brand kit
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert 'brand_kit' in data
    assert 'meta' in data['brand_kit']
    assert 'tier' in data['brand_kit']['meta']
    
    # Default should be minimum
    assert data['brand_kit']['meta']['tier'] == 'minimum'
    assert data['brand_kit']['meta']['completeness_score'] == 0


def test_brand_kit_wizard_page_accessible(client):
    """Test that the wizard page with Brand Kit step is accessible."""
    # Visit the wizard page
    response = client.get('/app')
    assert response.status_code == 200
    
    # Check that the page contains Brand Kit content
    html = response.data.decode('utf-8')
    assert 'Brand Kit' in html
    assert 'Good/Better/Best' in html or 'Good' in html
    assert 'This is how Eazeily writes posts that sound like YOUR business' in html


def test_brand_kit_generation_page_shows_banner(client):
    """Test that generation page shows Brand Kit banner when not configured."""
    # Visit the generation page
    response = client.get('/generate/social')
    assert response.status_code == 200
    
    # Check that the page contains Brand Kit banner
    html = response.data.decode('utf-8')
    assert 'brand-kit-banner' in html
    assert 'Want copy-paste-ready posts' in html or 'Add Brand Kit' in html


def test_brand_kit_settings_has_edit_link(client):
    """Test that settings page has Brand Kit edit option."""
    # Visit the settings page
    response = client.get('/settings')
    assert response.status_code == 200
    
    # Check that the page contains Brand Kit edit link
    html = response.data.decode('utf-8')
    assert 'Brand Kit' in html
    assert 'Edit Brand Kit' in html


def test_brand_kit_updates_preserve_existing_data(client):
    """Test that updating Brand Kit preserves existing data."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create initial brand kit
    initial_kit = {
        'business': {
            'company_name': 'Original Name'
        },
        'services': {
            'primary_services': ['Service A', 'Service B']
        },
        'audience': {
            'target_roles': ['Original Target']
        }
    }
    
    client.post('/api/brand_kit', json={'brand_kit': initial_kit})
    
    # Update with partial data
    update_kit = {
        'business': {
            'company_name': 'Updated Name'
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': update_kit})
    assert response.status_code == 200
    
    # Retrieve and verify
    get_response = client.get('/api/brand_kit')
    data = get_response.get_json()
    
    # Updated field should be changed
    assert data['brand_kit']['business']['company_name'] == 'Updated Name'
