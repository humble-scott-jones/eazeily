"""
Tests for the health check endpoint.
"""
import pytest
import json


def test_health_check_endpoint(client):
    """Test that health check endpoint returns 200 and expected structure."""
    resp = client.get('/_health')
    assert resp.status_code == 200
    
    data = json.loads(resp.data)
    assert 'status' in data
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'environment' in data


def test_health_check_does_not_leak_secrets(client):
    """Ensure health check doesn't expose any sensitive information."""
    resp = client.get('/_health')
    data = json.loads(resp.data)
    
    # Convert to string to check for common secret patterns
    response_str = json.dumps(data).lower()
    
    # Should not contain any secret-like strings
    assert 'secret' not in response_str
    assert 'password' not in response_str
    assert 'key' not in response_str or 'secret_key' not in response_str
    assert 'stripe' not in response_str
    assert 'sk_' not in response_str
    assert 'pk_' not in response_str
