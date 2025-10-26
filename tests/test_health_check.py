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
    # Check that 'key' is not present unless it's part of allowed fields
    # like 'secret_key' which shouldn't be in the response anyway
    if 'key' in response_str:
        # Allow only in benign contexts, fail if suspicious
        assert response_str.count('key') == 0 or all(
            word not in response_str 
            for word in ['secret_key', 'api_key', 'stripe']
        )
    assert 'sk_' not in response_str
    assert 'pk_' not in response_str
