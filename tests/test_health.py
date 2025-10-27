"""Tests for health check endpoint"""
from app import app


def test_health_check_endpoint_exists(client):
    """Test that health check endpoint is accessible"""
    response = client.get('/health')
    assert response.status_code in (200, 503)  # May be unhealthy in test env
    data = response.get_json()
    assert data is not None
    assert 'status' in data
    assert 'timestamp' in data
    assert 'checks' in data


def test_health_check_includes_database_status(client):
    """Test that health check includes database connectivity status"""
    response = client.get('/health')
    data = response.get_json()
    assert 'checks' in data
    assert 'database' in data['checks']
    # In test environment with proper fixtures, database should be connected
    assert data['checks']['database'] == 'connected'


def test_health_check_includes_service_status(client):
    """Test that health check includes external service status"""
    response = client.get('/health')
    data = response.get_json()
    assert 'checks' in data
    # Should include stripe and openai status
    assert 'stripe' in data['checks']
    assert 'openai' in data['checks']


def test_health_check_returns_200_when_healthy(client):
    """Test that health check returns 200 when all checks pass"""
    response = client.get('/health')
    data = response.get_json()
    if data['status'] == 'healthy':
        assert response.status_code == 200


def test_health_check_includes_version(client):
    """Test that health check includes version information"""
    response = client.get('/health')
    data = response.get_json()
    assert 'version' in data
