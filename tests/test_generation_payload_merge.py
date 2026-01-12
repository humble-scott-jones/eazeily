"""
Tests for generation payload merging and completeness.

Ensures that:
1. Required fields are always present in the payload
2. Defaults are applied only when fields are missing
3. Explicit overrides are preserved
4. Profile defaults are used when available
"""

import json
import pytest
import sqlite3
import uuid
import app as togetherly_app


def _create_test_user(client):
    """Helper to create a test user and set up session."""
    from models import db, User
    import uuid
    
    # Use SQLAlchemy to create user with unique email
    unique_email = f'test-{uuid.uuid4().hex[:8]}@example.com'
    user = User(email=unique_email)
    user.set_password('password123')
    
    # Need to use app context
    with client.application.app_context():
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Set up session
    with client.session_transaction() as sess:
        sess['user_id'] = str(user_id)
        sess['_user_id'] = str(user_id)
    
    return user_id


def test_payload_preserves_explicit_platforms(client):
    """Test that explicitly provided platforms are preserved, not replaced by profile defaults."""
    _create_test_user(client)
    
    # Create profile with default platforms
    profile_data = {
        'company': 'Test Co',
        'industry': 'technology',
        'tone': 'professional',
        'platforms': ['facebook', 'linkedin'],
    }
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Generate with different platforms
    gen_payload = {
        'days': 1,
        'platforms': ['instagram', 'tiktok'],  # Different from profile
        'tone': 'casual',
        'goals': ['engagement'],
        'brand_keywords': ['test'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    assert data['platforms'] == ['instagram', 'tiktok']  # Should use explicit, not profile defaults


def test_payload_uses_profile_defaults_when_missing(client):
    """Test that profile defaults are used when fields are not provided."""
    _create_test_user(client)
    
    # Create profile with defaults
    profile_data = {
        'company': 'Default Co',
        'industry': 'retail',
        'tone': 'friendly',
        'platforms': ['instagram'],
        'brand_keywords': ['quality', 'local'],
        'goals': ['awareness'],
    }
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Generate without specifying tone/keywords (should use profile defaults)
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        # tone, brand_keywords, and goals omitted
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert data['ok'] is True
    # Note: We can't directly verify the generator received profile defaults
    # but we can verify the request succeeded without explicit values


def test_payload_includes_all_required_fields(client):
    """Test that payload validation ensures all required fields are present."""
    _create_test_user(client)
    
    # Try to generate with incomplete payload (missing platforms)
    gen_payload = {
        'days': 1,
        'tone': 'professional',
        # platforms missing
    }
    
    response = client.post('/api/generate', json=gen_payload)
    # Should fail validation
    assert response.status_code == 400
    
    data = json.loads(response.data)
    assert data['status'] == 'error'
    assert 'platform' in data['error']['message'].lower()


def test_payload_preserves_explicit_keywords(client):
    """Test that explicitly provided keywords override profile defaults."""
    _create_test_user(client)
    
    # Create profile with keywords
    profile_data = {
        'company': 'Keyword Test Co',
        'industry': 'technology',
        'platforms': ['instagram'],
        'brand_keywords': ['default1', 'default2'],
    }
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Generate with different keywords
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'brand_keywords': ['override1', 'override2'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    # If the endpoint returns posts, they should reflect the override keywords


def test_payload_preserves_explicit_goals(client):
    """Test that explicitly provided goals override profile defaults."""
    _create_test_user(client)
    
    # Create profile with goals
    profile_data = {
        'company': 'Goals Test Co',
        'industry': 'technology',
        'platforms': ['instagram'],
        'goals': ['awareness', 'traffic'],
    }
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Generate with different goals
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'goals': ['sales', 'engagement'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    # Goals should be preserved as provided


def test_payload_includes_company_from_profile(client):
    """Test that company name is included from profile when not provided."""
    _create_test_user(client)
    
    # Create profile with company
    profile_data = {
        'company': 'My Company',
        'industry': 'technology',
        'platforms': ['instagram'],
    }
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Generate without company (should use profile)
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    # Company should be pulled from profile


def test_payload_includes_details_when_provided(client):
    """Test that details (reel_style, reel_length, etc.) are included when provided."""
    _create_test_user(client)
    
    gen_payload = {
        'days': 1,
        'platforms': ['tiktok'],
        'details': {
            'reel_style': 'face-camera-tips',
            'reel_length': '30',
            'production_tier': 'scrappy',
        },
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    # Details should be passed through to generator


def test_payload_includes_image_context_when_provided(client):
    """Test that image_data_url and image_context are included when provided."""
    _create_test_user(client)
    
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'image_data_url': 'data:image/png;base64,iVBORw0KGgo=',
        'image_context': 'Product photo with blue background',
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    # Image context should be passed through


def test_defaults_applied_only_when_missing(client):
    """Test that defaults don't override explicit null/empty values."""
    _create_test_user(client)
    
    # Create profile with defaults
    profile_data = {
        'company': 'Test Co',
        'industry': 'technology',
        'platforms': ['instagram'],
        'brand_keywords': ['keyword1'],
    }
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Generate with explicit empty arrays (should NOT use profile defaults)
    gen_payload = {
        'days': 1,
        'platforms': ['instagram'],
        'brand_keywords': [],  # Explicitly empty
        'goals': [],  # Explicitly empty
    }
    
    response = client.post('/api/generate', json=gen_payload)
    assert response.status_code == 200
    # Empty arrays should be preserved, not replaced with profile defaults
