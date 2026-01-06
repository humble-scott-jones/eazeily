"""Test marketing page integration with auth routes."""
import pytest
from app import create_app


@pytest.fixture
def client():
    """Create a test client."""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_index_renders_marketing_page(client):
    """Test that the root route renders the marketing page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Eazeily' in response.data
    assert b'Social Media' in response.data
    assert b'Made Simple' in response.data


def test_marketing_page_has_signin_link(client):
    """Test that the marketing page includes a Sign In link."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'/auth/login' in response.data
    assert b'Sign In' in response.data


def test_marketing_page_has_signup_link(client):
    """Test that the marketing page includes a Get Started link."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'/auth/signup' in response.data
    assert b'Get Started' in response.data


def test_signin_link_works(client):
    """Test that clicking Sign In takes you to the login page."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'Login' in response.data


def test_signup_link_works(client):
    """Test that clicking Get Started takes you to the signup page."""
    response = client.get('/auth/signup')
    assert response.status_code == 200
    assert b'Sign Up' in response.data
