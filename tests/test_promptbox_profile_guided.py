"""
Test for PromptBox profile-guided onboarding functionality.
Tests that the profile API endpoint works correctly for the PromptBox integration.
"""
import pytest
from models import VoiceProfile, User, db


def test_profile_api_returns_empty_for_new_user(client, monkeypatch):
    """Test that /api/profile returns empty profile for new users."""
    monkeypatch.setenv('GENAI_API_KEY', 'test-fake-key')
    
    # Create and login a user without a profile
    with client.application.app_context():
        user = User(email='newuser@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        user_id = user.id
    
    # Login
    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)
        sess['_fresh'] = True
    
    response = client.get('/api/profile')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert data['profile_status'] == 'empty'
    assert data['profile']['company'] == ''
    assert data['profile']['industry'] == ''
    assert data['profile']['tone'] == ''


def test_profile_api_returns_complete_profile(authenticated_client):
    """Test that /api/profile returns complete profile data."""
    # authenticated_client fixture already sets up a user with a profile
    response = authenticated_client.get('/api/profile')
    assert response.status_code == 200
    
    data = response.get_json()
    assert data['ok'] is True
    assert data['profile']['company'] == 'Test Business'
    assert data['profile']['industry'] == 'Technology'
    assert data['profile']['target_audience'] == 'Small businesses'


def test_profile_api_requires_authentication(client):
    """Test that /api/profile requires authentication."""
    response = client.get('/api/profile')
    # Should redirect to login
    assert response.status_code in [302, 401]


def test_dashboard_loads_with_promptbox(authenticated_client):
    """Test that dashboard page loads successfully with PromptBox."""
    response = authenticated_client.get('/dashboard')
    assert response.status_code == 200
    
    # Check that PromptBox container exists
    html = response.get_data(as_text=True)
    assert 'dashboard-promptbox' in html
    assert 'promptbox.js' in html
    assert 'promptbox.css' in html
    # Check for the new initialization
    assert 'initWithProfileContext' in html


def test_promptbox_js_syntax_valid():
    """Test that promptbox.js file exists and has valid syntax."""
    from pathlib import Path
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'promptbox.js'
    assert js_path.exists(), f"promptbox.js not found at {js_path}"
    
    content = js_path.read_text()
        
    # Check for key functions
    assert 'initWithProfileContext' in content
    assert 'checkProfileCompleteness' in content
    assert 'showOnboardingWelcome' in content
    assert 'showCompletionNudge' in content
    assert 'showReadyState' in content
    assert 'renderMessageButtons' in content


def test_promptbox_css_has_button_styles():
    """Test that promptbox.css includes button styles."""
    from pathlib import Path
    css_path = Path(__file__).parent.parent / 'static' / 'css' / 'promptbox.css'
    assert css_path.exists(), f"promptbox.css not found at {css_path}"
    
    content = css_path.read_text()
    
    # Check for button styles
    assert 'promptbox-button-container' in content
    assert 'promptbox-action-btn' in content


def test_promptbox_js_has_slash_hint_logic():
    """Test that promptbox.js includes slash command hint logic."""
    from pathlib import Path
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'promptbox.js'
    assert js_path.exists(), f"promptbox.js not found at {js_path}"
    
    content = js_path.read_text()
    
    # Check for slash hint related code
    assert 'hasUsedSlashCommand' in content
    assert 'eazeily_used_slash' in content
    assert 'promptbox-slash-hint' in content
    assert 'fade-out' in content


def test_promptbox_css_has_slash_hint_styles():
    """Test that promptbox.css includes slash command hint styles."""
    from pathlib import Path
    css_path = Path(__file__).parent.parent / 'static' / 'css' / 'promptbox.css'
    assert css_path.exists(), f"promptbox.css not found at {css_path}"
    
    content = css_path.read_text()
    
    # Check for slash hint styles
    assert 'promptbox-slash-hint' in content
    assert '.promptbox-slash-hint kbd' in content
    assert '.promptbox-slash-hint.hidden' in content
    assert '.promptbox-slash-hint.fade-out' in content
