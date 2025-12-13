"""
Test that generator pages include required scripts and don't have ReferenceErrors.

This test ensures the publishingQueueState bug never returns.
"""
import pytest
from app import app


@pytest.fixture
def client():
    """Create a test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_generate_social_page_loads(client):
    """Verify /generate/social returns 200."""
    response = client.get('/generate/social')
    assert response.status_code == 200
    assert b'Generate Content' in response.data


def test_generate_social_includes_dashboard_js(client):
    """Verify /generate/social includes dashboard.js script."""
    response = client.get('/generate/social')
    assert response.status_code == 200
    assert b'/static/dashboard.js' in response.data


def test_generate_social_includes_app_js(client):
    """Verify /generate/social includes app.js script."""
    response = client.get('/generate/social')
    assert response.status_code == 200
    assert b'/static/app.js' in response.data


def test_generate_reels_page_loads(client):
    """Verify /generate/reels returns 200."""
    response = client.get('/generate/reels')
    assert response.status_code == 200
    # Reels page has its own structure
    assert b'Reels' in response.data


def test_generate_reviews_page_loads(client):
    """Verify /generate/reviews returns 200."""
    response = client.get('/generate/reviews')
    assert response.status_code == 200
    assert b'Review Response Generator' in response.data


def test_dashboard_js_declares_publishing_queue_state():
    """Verify dashboard.js declares publishingQueueState variable."""
    import pathlib
    dashboard_js = pathlib.Path(__file__).parent.parent / 'static' / 'dashboard.js'
    content = dashboard_js.read_text()
    
    # Check that publishingQueueState is declared
    assert 'publishingQueueState' in content, "publishingQueueState must be declared in dashboard.js"
    
    # Check that it's declared as a const/let/var with initialization
    assert ('const publishingQueueState = {' in content or 
            'let publishingQueueState = {' in content or 
            'var publishingQueueState = {' in content), \
        "publishingQueueState must be declared with initialization"
    
    # Check that it has an entries array
    assert 'entries: []' in content, "publishingQueueState should have an entries array"
    
    # Check that PUBLISHING_QUEUE_STORAGE_KEY is declared
    assert 'PUBLISHING_QUEUE_STORAGE_KEY' in content, "PUBLISHING_QUEUE_STORAGE_KEY constant must be declared"


def test_dashboard_js_has_defensive_guards():
    """Verify dashboard.js has defensive guards for publishingQueueState."""
    import pathlib
    dashboard_js = pathlib.Path(__file__).parent.parent / 'static' / 'dashboard.js'
    content = dashboard_js.read_text()
    
    # Check that there are guards checking if publishingQueueState exists
    assert '!publishingQueueState' in content or 'publishingQueueState ||' in content, \
        "dashboard.js should have defensive guards for publishingQueueState"
    
    # Check that guards check for entries array
    assert 'Array.isArray(publishingQueueState.entries)' in content, \
        "dashboard.js should check if publishingQueueState.entries is an array"
