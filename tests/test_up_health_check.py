"""Test the /up health check endpoint for Railway deployment."""


def test_up_health_check_returns_200(client):
    """Test that /up endpoint returns 200 OK for Railway health checks."""
    response = client.get('/up')
    assert response.status_code == 200
    assert response.data == b'OK'


def test_up_health_check_no_auth_required(client):
    """Test that /up endpoint does not require authentication."""
    # No authentication headers or login
    response = client.get('/up')
    assert response.status_code == 200
