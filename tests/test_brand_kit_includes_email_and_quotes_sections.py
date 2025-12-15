"""Test that Brand Kit includes email and quotes sections for fast-follow generators."""

import pytest
import json


def test_brand_kit_includes_email_section(client):
    """Test that brand kit includes email section."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    data = response.get_json()
    brand_kit = data['brand_kit']
    
    assert 'email' in brand_kit
    assert isinstance(brand_kit['email'], dict)


def test_brand_kit_includes_quotes_section(client):
    """Test that brand kit includes quotes section."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    data = response.get_json()
    brand_kit = data['brand_kit']
    
    assert 'quotes' in brand_kit
    assert isinstance(brand_kit['quotes'], dict)


def test_email_section_has_sender_fields(client):
    """Test email section includes sender customization fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    email = brand_kit['email']
    
    # Sender fields
    assert 'sender_name' in email
    assert 'signoff_style' in email
    assert 'signature_lines' in email


def test_email_section_has_cta_and_links(client):
    """Test email section includes CTA and links for email templates."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    email = brand_kit['email']
    
    # CTA and links for email generation
    assert 'preferred_cta' in email
    assert 'links' in email


def test_quotes_section_has_validity_fields(client):
    """Test quotes section includes validity and deposit fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    quotes = brand_kit['quotes']
    
    # Validity and deposit
    assert 'default_validity_days' in quotes
    assert 'deposit_policy' in quotes


def test_quotes_section_has_payment_fields(client):
    """Test quotes section includes payment and turnaround fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    quotes = brand_kit['quotes']
    
    # Payment and timing
    assert 'payment_methods' in quotes
    assert 'turnaround_time' in quotes


def test_quotes_section_has_terms_fields(client):
    """Test quotes section includes terms and disclaimer fields."""
    response = client.get('/api/brand_kit')
    assert response.status_code == 200
    
    brand_kit = response.get_json()['brand_kit']
    quotes = brand_kit['quotes']
    
    # Terms and legal
    assert 'terms_bullets' in quotes
    assert 'disclaimer' in quotes


def test_email_section_can_be_saved_and_retrieved(client):
    """Test that email section data can be saved and retrieved."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Save brand kit with email data
    brand_kit = {
        'business': {
            'company_name': 'Email Test Co'
        },
        'email': {
            'sender_name': 'Sarah from Email Test',
            'signoff_style': 'warm',
            'signature_lines': ['Warmly,', 'Sarah', 'Founder, Email Test Co'],
            'preferred_cta': 'book',
            'links': {
                'booking': 'https://example.com/book',
                'menu': 'https://example.com/menu'
            }
        }
    }
    
    post_response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert post_response.status_code == 200
    
    # Retrieve and verify
    get_response = client.get('/api/brand_kit')
    assert get_response.status_code == 200
    
    retrieved = get_response.get_json()['brand_kit']
    email = retrieved['email']
    
    assert email['sender_name'] == 'Sarah from Email Test'
    assert email['signoff_style'] == 'warm'
    assert email['signature_lines'] == ['Warmly,', 'Sarah', 'Founder, Email Test Co']
    assert email['preferred_cta'] == 'book'
    assert email['links']['booking'] == 'https://example.com/book'
    assert email['links']['menu'] == 'https://example.com/menu'


def test_quotes_section_can_be_saved_and_retrieved(client):
    """Test that quotes section data can be saved and retrieved."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Save brand kit with quotes data
    brand_kit = {
        'business': {
            'company_name': 'Quote Test Co'
        },
        'quotes': {
            'default_validity_days': 14,
            'deposit_policy': '50% deposit required upfront',
            'payment_methods': ['credit_card', 'cash', 'check'],
            'turnaround_time': '2-3 business days',
            'terms_bullets': [
                'Cancellations require 24h notice',
                'Rescheduling allowed once',
                'Final payment due upon completion'
            ],
            'disclaimer': 'Prices subject to change. Standard terms apply.'
        }
    }
    
    post_response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert post_response.status_code == 200
    
    # Retrieve and verify
    get_response = client.get('/api/brand_kit')
    assert get_response.status_code == 200
    
    retrieved = get_response.get_json()['brand_kit']
    quotes = retrieved['quotes']
    
    assert quotes['default_validity_days'] == 14
    assert quotes['deposit_policy'] == '50% deposit required upfront'
    assert quotes['payment_methods'] == ['credit_card', 'cash', 'check']
    assert quotes['turnaround_time'] == '2-3 business days'
    assert len(quotes['terms_bullets']) == 3
    assert quotes['disclaimer'] == 'Prices subject to change. Standard terms apply.'


def test_email_and_quotes_are_optional_fields(client):
    """Test that email and quotes sections can be left empty."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Save brand kit without email/quotes details
    brand_kit = {
        'business': {
            'company_name': 'Minimal Co',
            'industry_id': 'retail'
        },
        'services': {
            'primary_services': ['Service 1', 'Service 2']
        }
    }
    
    post_response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert post_response.status_code == 200
    
    # Should still have sections but with null/empty values
    get_response = client.get('/api/brand_kit')
    assert get_response.status_code == 200
    
    retrieved = get_response.get_json()['brand_kit']
    
    # Sections exist but are empty/null
    assert 'email' in retrieved
    assert 'quotes' in retrieved
    
    # Fields should be null or empty
    email = retrieved['email']
    assert email['sender_name'] is None
    assert email['signoff_style'] is None
    
    quotes = retrieved['quotes']
    assert quotes['default_validity_days'] is None
    assert quotes['deposit_policy'] is None


def test_brand_kit_with_all_sections_filled(client):
    """Test a complete brand kit with all sections including email and quotes."""
    # Sign up a user
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Save comprehensive brand kit
    brand_kit = {
        'business': {
            'company_name': 'Complete Co',
            'industry_id': 'fitness',
            'service_area': 'San Francisco, CA',
            'timezone': 'America/Los_Angeles',
            'booking_url': 'https://complete.co/book',
            'contact_email': 'hello@complete.co',
            'contact_phone': '(555) 123-4567'
        },
        'services': {
            'primary_services': ['Personal Training', 'Group Classes'],
            'addons': ['Nutrition Coaching', 'Online Access'],
            'pricing_style': 'membership',
            'service_constraints': ['24h cancellation required']
        },
        'audience': {
            'target_roles': ['Busy professionals', 'Parents'],
            'top_pains': ['No time', 'Lack motivation', 'Previous injuries'],
            'desired_outcomes': ['Get fit', 'Feel energized', 'Build strength'],
            'sophistication': 'beginner',
            'objections': ['Too expensive', 'Not enough time']
        },
        'positioning': {
            'differentiators': ['Personal attention', 'Flexible scheduling'],
            'values': ['Health first', 'Community'],
            'boundaries': ['No refunds after session start']
        },
        'proof': {
            'credentials': ['NASM Certified', 'CPR Certified'],
            'years_in_business': 5,
            'volume_markers': [{'label': 'Clients trained', 'value': '200+'}],
            'testimonials': ['Changed my life!']
        },
        'email': {
            'sender_name': 'Coach Mike',
            'signoff_style': 'warm',
            'signature_lines': ['Stay strong,', 'Coach Mike'],
            'preferred_cta': 'book',
            'links': {
                'booking': 'https://complete.co/book',
                'menu': 'https://complete.co/classes'
            }
        },
        'quotes': {
            'default_validity_days': 7,
            'deposit_policy': 'First session payment upfront',
            'payment_methods': ['card', 'venmo'],
            'turnaround_time': 'Same day',
            'terms_bullets': ['24h cancellation', 'Packages non-refundable'],
            'disclaimer': 'Consult doctor before starting'
        },
        'assets': {
            'logo_url': 'https://complete.co/logo.png'
        }
    }
    
    post_response = client.post('/api/brand_kit', json={'brand_kit': brand_kit})
    assert post_response.status_code == 200
    
    data = post_response.get_json()
    assert data['ok'] is True
    
    # Verify all sections were saved
    saved_kit = data['brand_kit']
    assert saved_kit['email']['sender_name'] == 'Coach Mike'
    assert saved_kit['quotes']['default_validity_days'] == 7
    assert saved_kit['meta']['tier'] in ['minimum', 'stronger', 'best']
    assert saved_kit['meta']['completeness_score'] > 50
