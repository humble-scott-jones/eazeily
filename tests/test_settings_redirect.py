"""Test that /settings route redirects to /profile."""


def test_settings_requires_authentication(client):
    """Test that /settings redirects to login when not authenticated."""
    response = client.get('/settings')
    assert response.status_code == 302
    assert '/auth/login' in response.location


def test_settings_redirects_to_profile(authenticated_client):
    """Test that /settings redirects to /profile when authenticated."""
    response = authenticated_client.get('/settings', follow_redirects=False)
    assert response.status_code == 302
    assert response.location.endswith('/profile')


def test_settings_redirect_chain_to_profile(authenticated_client):
    """Test that /settings ultimately leads to /profile page."""
    response = authenticated_client.get('/settings', follow_redirects=True)
    assert response.status_code == 200
    # Verify we're on the profile page by checking for profile-specific content
    assert b'Brand Profile' in response.data or b'profile' in response.data.lower()
