"""
Test enhanced error reporting for /api/profile GET route.

This test ensures that:
1. In non-production mode (FLASK_ENV=development, test, staging or ALLOW_DEV_DEBUG=1),
   error responses include debug details (exception type and message)
2. In production mode, error responses do not include debug details
3. request_id is always present in error responses
"""
import pytest
from models import VoiceProfile, db
from unittest.mock import patch, MagicMock


def test_profile_load_error_includes_debug_in_dev_mode(authenticated_client, monkeypatch):
    """Test that errors include debug info in development/staging mode."""
    # Set non-production environment
    monkeypatch.setenv('FLASK_ENV', 'development')
    
    # Mock VoiceProfile.query.filter_by to raise an exception
    with patch('routes.profile_routes.VoiceProfile') as mock_voice_profile:
        mock_query = MagicMock()
        mock_query.filter_by.side_effect = RuntimeError('Simulated database connection failure')
        mock_voice_profile.query = mock_query
        
        # Make request
        response = authenticated_client.get('/api/profile')
    
    # Verify response structure
    assert response.status_code == 500
    data = response.get_json()
    
    # Base error structure should be present
    assert data.get('ok') is False
    assert data.get('request_id') is not None
    assert 'error' in data
    assert data['error'].get('code') == 'profile_load_error'
    assert data['error'].get('message') == 'Failed to load profile'
    
    # Debug information should be present in non-production mode
    assert 'debug' in data, "Debug field should be present in non-production mode"
    assert 'exception_type' in data['debug']
    assert 'exception_message' in data['debug']
    assert data['debug']['exception_type'] == 'RuntimeError'
    assert 'Simulated database connection failure' in data['debug']['exception_message']


def test_profile_load_error_excludes_debug_in_production_mode(authenticated_client, monkeypatch):
    """Test that errors DO NOT include debug info in production mode."""
    # Set production environment (explicitly set to production, no DEBUG flags)
    monkeypatch.setenv('FLASK_ENV', 'production')
    monkeypatch.delenv('ALLOW_DEV_DEBUG', raising=False)
    
    # Mock VoiceProfile.query.filter_by to raise an exception
    with patch('routes.profile_routes.VoiceProfile') as mock_voice_profile:
        mock_query = MagicMock()
        mock_query.filter_by.side_effect = RuntimeError('Simulated database connection failure')
        mock_voice_profile.query = mock_query
        
        # Make request
        response = authenticated_client.get('/api/profile')
    
    # Verify response structure
    assert response.status_code == 500
    data = response.get_json()
    
    # Base error structure should be present
    assert data.get('ok') is False
    assert data.get('request_id') is not None
    assert 'error' in data
    assert data['error'].get('code') == 'profile_load_error'
    assert data['error'].get('message') == 'Failed to load profile'
    
    # Debug information should NOT be present in production mode
    assert 'debug' not in data, "Debug field should NOT be present in production mode"


def test_profile_load_error_includes_debug_with_allow_dev_debug_flag(authenticated_client, monkeypatch):
    """Test that errors include debug info when ALLOW_DEV_DEBUG=1 is set."""
    # Set ALLOW_DEV_DEBUG flag (even without FLASK_ENV)
    monkeypatch.setenv('ALLOW_DEV_DEBUG', '1')
    monkeypatch.delenv('FLASK_ENV', raising=False)
    
    # Mock VoiceProfile.query.filter_by to raise an exception
    with patch('routes.profile_routes.VoiceProfile') as mock_voice_profile:
        mock_query = MagicMock()
        mock_query.filter_by.side_effect = ValueError('Another test exception')
        mock_voice_profile.query = mock_query
        
        # Make request
        response = authenticated_client.get('/api/profile')
    
    # Verify response structure
    assert response.status_code == 500
    data = response.get_json()
    
    # Debug information should be present with ALLOW_DEV_DEBUG
    assert 'debug' in data, "Debug field should be present with ALLOW_DEV_DEBUG=1"
    assert data['debug']['exception_type'] == 'ValueError'
    assert 'Another test exception' in data['debug']['exception_message']


def test_profile_load_error_includes_debug_in_staging(authenticated_client, monkeypatch):
    """Test that errors include debug info in staging environment."""
    # Set staging environment
    monkeypatch.setenv('FLASK_ENV', 'staging')
    
    # Mock VoiceProfile.query.filter_by to raise an exception
    with patch('routes.profile_routes.VoiceProfile') as mock_voice_profile:
        mock_query = MagicMock()
        mock_query.filter_by.side_effect = ConnectionError('Database connection timeout')
        mock_voice_profile.query = mock_query
        
        # Make request
        response = authenticated_client.get('/api/profile')
    
    # Verify response structure
    assert response.status_code == 500
    data = response.get_json()
    
    # Debug information should be present in staging
    assert 'debug' in data, "Debug field should be present in staging mode"
    assert data['debug']['exception_type'] == 'ConnectionError'
    assert 'Database connection timeout' in data['debug']['exception_message']


def test_profile_load_success_has_no_debug_field(authenticated_client):
    """Test that successful responses don't have a debug field."""
    # Make a successful request
    response = authenticated_client.get('/api/profile')
    
    # Verify successful response
    assert response.status_code == 200
    data = response.get_json()
    
    # Successful response should not have debug field
    assert data.get('ok') is True
    assert 'debug' not in data, "Debug field should not be in successful responses"
    assert data.get('request_id') is not None
