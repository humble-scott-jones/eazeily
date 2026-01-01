"""Test the /healthz health check endpoint for Railway deployment."""
import pytest
from app import app as flask_app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


def test_healthz_health_check_returns_200(client):
    """Test that /healthz endpoint returns 200 OK for Railway health checks."""
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.data == b'OK'


def test_healthz_health_check_no_auth_required(client):
    """Test that /healthz endpoint does not require authentication."""
    # No authentication headers or login
    response = client.get('/healthz')
    assert response.status_code == 200
