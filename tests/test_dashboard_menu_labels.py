"""Test dashboard menu labels for clarity."""
import pytest
from pathlib import Path


def test_dashboard_template_has_clear_profile_labels():
    """Test that dashboard template has clear labels for View Profile and Edit Profile."""
    # Read the template file directly
    template_path = Path(__file__).parent.parent / 'templates' / 'dashboard.html'
    html = template_path.read_text()
    
    # Check for "View Profile" with chat action
    assert 'View Profile' in html, "Should have 'View Profile' label"
    assert "menuAction('profile')" in html, "Should have menuAction for profile"
    
    # Check for "Edit Profile" with link to /profile
    assert 'Edit Profile' in html, "Should have 'Edit Profile' label"
    assert 'href="/profile"' in html, "Should have link to /profile"
    
    # Check for the edit icon (pencil emoji)
    assert '✏️' in html, "Should have pencil emoji icon"
    
    # Check for tooltips/accessibility
    assert 'View your profile summary in chat' in html, "Should have tooltip for View Profile"
    assert 'Edit your profile information' in html, "Should have tooltip for Edit Profile"
    
    # Verify old labels are removed
    assert '<span>Profile</span>' not in html, "Should not have old 'Profile' label"
    assert '<span>Settings</span>' not in html, "Should not have old 'Settings' label"
    assert '⚙️' not in html, "Should not have settings gear icon"


def test_dashboard_template_menu_structure():
    """Test that dashboard menu maintains correct structure."""
    template_path = Path(__file__).parent.parent / 'templates' / 'dashboard.html'
    html = template_path.read_text()
    
    # Check menu structure is intact
    assert 'class="menu-items"' in html
    assert 'id="menu-profile-badge"' in html
    assert 'class="menu-badge"' in html
    
    # Verify the order: View Profile, Content Calendar, Edit Profile
    view_profile_pos = html.find('View Profile')
    content_calendar_pos = html.find('Content Calendar')
    edit_profile_pos = html.find('Edit Profile')
    
    assert view_profile_pos < content_calendar_pos < edit_profile_pos, \
        "Menu items should be in order: View Profile, Content Calendar, Edit Profile"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
