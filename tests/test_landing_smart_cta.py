"""Tests for smart CTAs on landing page."""
import json


def test_landing_page_has_smart_cta_logic(client):
    """Test that landing page includes smart CTA logic for logged in/out users."""
    response = client.get('/')
    assert response.status_code == 200
    # Check for Jinja2 template logic
    assert b'current_user.is_authenticated' in response.data
    assert b'Go to Dashboard' in response.data
    assert b'Start for Free' in response.data or b'Get Started' in response.data


def test_landing_page_no_pricing_references(client):
    """Test that landing page has no specific pricing or lifetime deal mentions."""
    response = client.get('/')
    assert response.status_code == 200
    # Should not contain old pricing references
    assert b'$67' not in response.data
    assert b'lifetime pricing' not in response.data.lower()
    assert b'one-time payment' not in response.data.lower()


def test_landing_page_no_waitlist_forms(client):
    """Test that landing page no longer has waitlist forms."""
    response = client.get('/')
    assert response.status_code == 200
    # Should not contain waitlist form IDs
    assert b'launch-waitlist-form' not in response.data
    assert b'final-waitlist-form' not in response.data


def test_landing_page_shows_now_available(client):
    """Test that landing page shows 'Now Available' instead of 'Launching Soon'."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Now Available' in response.data
    assert b'Launching Soon' not in response.data or b'Join the Waitlist' not in response.data


def test_landing_page_has_generate_post_cta(client):
    """Test that landing page includes 'Generate Post' CTA for authenticated users."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Generate Post' in response.data
