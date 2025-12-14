"""Tests for the industry pack good_defaults API endpoint contract."""

import pytest
import json


def test_good_defaults_endpoint_returns_expected_structure(client):
    """Test that GET /api/industry_packs/{industry_id}/good_defaults returns expected structure."""
    # Test with a known industry (salon)
    response = client.get('/api/industry_packs/salon/good_defaults')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Verify top-level structure
    assert data['ok'] is True
    assert 'request_id' in data
    assert data['industry_id'] == 'salon'
    assert 'good_defaults' in data
    
    # Verify good_defaults structure
    good_defaults = data['good_defaults']
    assert 'chip_presets' in good_defaults
    assert 'audience' in good_defaults
    assert 'offers' in good_defaults
    assert 'proof' in good_defaults
    
    # Verify chip_presets structure
    chip_presets = good_defaults['chip_presets']
    assert 'focus_topics' in chip_presets
    assert 'audience_chips' in chip_presets
    assert 'offer_chips' in chip_presets
    assert 'proof_chips' in chip_presets
    
    # Verify chips are normalized to {id, label} format
    for chip_category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        chips = chip_presets[chip_category]
        assert isinstance(chips, list)
        assert len(chips) > 0
        for chip in chips:
            assert isinstance(chip, dict)
            assert 'id' in chip
            assert 'label' in chip


def test_good_defaults_endpoint_with_general_industry(client):
    """Test that general industry returns defaults."""
    response = client.get('/api/industry_packs/general/good_defaults')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['ok'] is True
    assert data['industry_id'] == 'general'
    assert 'good_defaults' in data


def test_good_defaults_endpoint_with_unknown_industry_fallback(client):
    """Test that unknown industry falls back to general."""
    response = client.get('/api/industry_packs/unknown_industry_xyz/good_defaults')
    
    # Should succeed with fallback to general
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['ok'] is True
    assert data['industry_id'] == 'unknown_industry_xyz'
    # Should still return good_defaults (from general fallback)
    assert 'good_defaults' in data


def test_profile_save_with_chip_selections(client):
    """Test that profile can save chip selection IDs."""
    # Create a session with profile_id
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-profile-id'
    
    # Save profile with chip selections
    payload = {
        'industry': 'salon',
        'company': 'Test Salon',
        'tone': 'friendly',
        'platforms': ['instagram', 'facebook'],
        'selected_focus_topic_ids': ['hair_transformations', 'color_services'],
        'selected_audience_ids': ['women_seeking_color', 'first_time_clients'],
        'selected_offer_ids': ['free_consultation', 'new_client_discount'],
        'selected_proof_ids': ['certified_colorists', '5_star_rated'],
        'selected_cta_intent_id': 'booking'
    }
    
    response = client.post('/api/profile',
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['ok'] is True
    
    # Verify we can retrieve the saved selections
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['ok'] is True
    profile = data['profile']
    assert profile['selected_focus_topic_ids'] == ['hair_transformations', 'color_services']
    assert profile['selected_audience_ids'] == ['women_seeking_color', 'first_time_clients']
    assert profile['selected_offer_ids'] == ['free_consultation', 'new_client_discount']
    assert profile['selected_proof_ids'] == ['certified_colorists', '5_star_rated']
    assert profile['selected_cta_intent_id'] == 'booking'


def test_profile_get_returns_chip_selections_in_structure(client):
    """Test that GET /api/profile includes chip selection fields in response."""
    # Create a session with profile_id
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-profile-id-2'
    
    # Get empty profile (should have empty arrays for chip selections)
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['ok'] is True
    profile = data['profile']
    
    # Should have chip selection fields with default values
    assert 'selected_focus_topic_ids' in profile
    assert 'selected_audience_ids' in profile
    assert 'selected_offer_ids' in profile
    assert 'selected_proof_ids' in profile
    assert 'selected_cta_intent_id' in profile
    
    # Default values should be empty arrays or None
    assert profile['selected_focus_topic_ids'] == []
    assert profile['selected_audience_ids'] == []
    assert profile['selected_offer_ids'] == []
    assert profile['selected_proof_ids'] == []
    assert profile['selected_cta_intent_id'] is None
