"""Test Brand Kit v1 schema validation and completeness scoring."""

import pytest
import json


def test_brand_kit_has_all_required_sections(client):
    """Test that default brand kit includes all required sections."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert 'brand_kit' in data
    
    brand_kit = data['brand_kit']
    
    # Verify structure
    assert brand_kit['version'] == 1
    assert 'business' in brand_kit
    assert 'services' in brand_kit
    assert 'audience' in brand_kit
    assert 'positioning' in brand_kit
    assert 'proof' in brand_kit
    assert 'email' in brand_kit
    assert 'quotes' in brand_kit
    assert 'assets' in brand_kit
    assert 'meta' in brand_kit


def test_brand_kit_business_section_structure(client):
    """Test business section has expected fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    business = brand_kit['business']
    
    assert 'company_name' in business
    assert 'industry_id' in business
    assert 'service_area' in business
    assert 'timezone' in business
    assert 'booking_url' in business
    assert 'contact_email' in business
    assert 'contact_phone' in business


def test_brand_kit_services_section_structure(client):
    """Test services section has expected fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    services = brand_kit['services']
    
    assert 'primary_services' in services
    assert isinstance(services['primary_services'], list)
    assert 'addons' in services
    assert isinstance(services['addons'], list)
    assert 'pricing_style' in services
    assert 'service_constraints' in services
    assert isinstance(services['service_constraints'], list)


def test_brand_kit_audience_section_structure(client):
    """Test audience section has expected fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    audience = brand_kit['audience']
    
    assert 'target_roles' in audience
    assert isinstance(audience['target_roles'], list)
    assert 'top_pains' in audience
    assert isinstance(audience['top_pains'], list)
    assert 'desired_outcomes' in audience
    assert isinstance(audience['desired_outcomes'], list)
    assert 'sophistication' in audience
    assert 'objections' in audience
    assert isinstance(audience['objections'], list)


def test_brand_kit_positioning_section_structure(client):
    """Test positioning section has expected fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    positioning = brand_kit['positioning']
    
    assert 'differentiators' in positioning
    assert isinstance(positioning['differentiators'], list)
    assert 'values' in positioning
    assert isinstance(positioning['values'], list)
    assert 'boundaries' in positioning
    assert isinstance(positioning['boundaries'], list)


def test_brand_kit_proof_section_structure(client):
    """Test proof section has expected fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    proof = brand_kit['proof']
    
    assert 'credentials' in proof
    assert isinstance(proof['credentials'], list)
    assert 'years_in_business' in proof
    assert 'volume_markers' in proof
    assert 'testimonials' in proof


def test_brand_kit_email_section_structure(client):
    """Test email section has expected fields for email generator."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    email = brand_kit['email']
    
    assert 'sender_name' in email
    assert 'signoff_style' in email
    assert 'signature_lines' in email
    assert 'preferred_cta' in email
    assert 'links' in email


def test_brand_kit_quotes_section_structure(client):
    """Test quotes section has expected fields for quote generator."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    quotes = brand_kit['quotes']
    
    assert 'default_validity_days' in quotes
    assert 'deposit_policy' in quotes
    assert 'payment_methods' in quotes
    assert 'turnaround_time' in quotes
    assert 'terms_bullets' in quotes
    assert 'disclaimer' in quotes


def test_brand_kit_meta_section_has_tier_and_score(client):
    """Test meta section includes tier and completeness score."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    meta = brand_kit['meta']
    
    assert 'tier' in meta
    assert meta['tier'] in ['minimum', 'stronger', 'best']
    assert 'completeness_score' in meta
    assert isinstance(meta['completeness_score'], (int, float))
    assert 0 <= meta['completeness_score'] <= 100
    assert 'updated_at' in meta


def test_empty_brand_kit_has_minimum_tier(client):
    """Test that an empty brand kit defaults to minimum tier with 0 score."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    meta = brand_kit['meta']
    
    assert meta['tier'] == 'minimum'
    assert meta['completeness_score'] == 0


def test_brand_kit_completeness_scoring_with_partial_data(client):
    """Test that completeness score increases with more filled sections."""
    # First, sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Save a partially filled brand kit
    partial_kit = {
        'business': {
            'company_name': 'Test Company',
            'industry_id': 'retail',
            'contact_email': 'test@example.com'
        },
        'services': {
            'primary_services': ['Service 1', 'Service 2']
        },
        'audience': {
            'target_roles': ['Small business owners'],
            'top_pains': ['Not enough time'],
            'desired_outcomes': ['More customers']
        },
        'positioning': {
            'differentiators': ['Fast', 'Reliable']
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': partial_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    
    brand_kit = data['brand_kit']
    meta = brand_kit['meta']
    
    # Should have at least minimum tier with basic requirements met
    assert meta['tier'] in ['minimum', 'stronger', 'best']
    # Score should be > 0 since we have some data
    assert meta['completeness_score'] > 0
    assert meta['completeness_score'] < 100


def test_brand_kit_completeness_best_tier(client):
    """Test that a well-filled brand kit achieves best tier."""
    # First, sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Save a comprehensive brand kit
    comprehensive_kit = {
        'business': {
            'company_name': 'Premium Company',
            'industry_id': 'retail',
            'service_area': 'Los Angeles, CA',
            'timezone': 'America/Los_Angeles',
            'booking_url': 'https://example.com/book',
            'contact_email': 'hello@example.com',
            'contact_phone': '555-1234'
        },
        'services': {
            'primary_services': ['Service 1', 'Service 2', 'Service 3'],
            'addons': ['Extra 1', 'Extra 2'],
            'pricing_style': 'starting_at',
            'service_constraints': ['No same-day']
        },
        'audience': {
            'target_roles': ['Business owners', 'Managers'],
            'top_pains': ['Time', 'Budget', 'Quality'],
            'desired_outcomes': ['Growth', 'Efficiency'],
            'sophistication': 'intermediate',
            'objections': ['Too expensive']
        },
        'positioning': {
            'differentiators': ['Fast', 'Reliable', 'Affordable'],
            'values': ['Honesty', 'Quality'],
            'boundaries': ['No refunds after 24h']
        },
        'proof': {
            'credentials': ['Certified', 'Licensed'],
            'years_in_business': 10,
            'volume_markers': [{'label': 'Clients', 'value': '500+'}],
            'testimonials': ['Great service!']
        },
        'email': {
            'sender_name': 'John from Premium',
            'signoff_style': 'professional',
            'signature_lines': ['Best regards'],
            'preferred_cta': 'book',
            'links': {'booking': 'https://example.com/book'}
        },
        'quotes': {
            'default_validity_days': 14,
            'deposit_policy': '50% upfront',
            'payment_methods': ['card', 'cash'],
            'turnaround_time': '2-3 days',
            'terms_bullets': ['No refunds'],
            'disclaimer': 'Standard terms apply'
        }
    }
    
    response = client.post('/api/brand_kit', json={'brand_kit': comprehensive_kit})
    assert response.status_code == 200
    
    data = response.get_json()
    brand_kit = data['brand_kit']
    meta = brand_kit['meta']
    
    # Should achieve best tier with high completeness
    assert meta['tier'] == 'best'
    assert meta['completeness_score'] >= 75
