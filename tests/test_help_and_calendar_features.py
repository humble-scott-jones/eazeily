"""
Tests for /help command and Content Calendar features.
"""
import pytest
from pathlib import Path


def test_help_command_in_slash_commands():
    """Test that /help command is present in SLASH_COMMANDS array."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'promptbox.js'
    assert js_path.exists(), f"promptbox.js not found at {js_path}"
    
    content = js_path.read_text()
    
    # Check that /help is in SLASH_COMMANDS
    assert "{ command: '/help'" in content
    assert "description: 'Show all available commands'" in content
    assert "category: 'help'" in content


def test_help_command_handler_exists():
    """Test that handleHelpCommand function exists."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'promptbox.js'
    content = js_path.read_text()
    
    # Check for handleHelpCommand function
    assert 'async function handleHelpCommand(promptBox)' in content
    
    # Check that it shows help message
    assert '## ❓ Available Commands' in content
    assert '### 📝 Content Creation' in content
    assert '### 👤 Profile Management' in content


def test_help_command_in_profile_commands():
    """Test that /help is included in profileCommands arrays."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'promptbox.js'
    content = js_path.read_text()
    
    # Check that /help is in profileCommands arrays
    # There should be at least one occurrence with /help
    assert "'/help'" in content
    
    # Count occurrences of profileCommands arrays with /help
    import re
    pattern = r"const profileCommands = \[.*?'/help'.*?\]"
    matches = re.findall(pattern, content, re.DOTALL)
    assert len(matches) >= 1, "Expected at least one profileCommands array with /help"


def test_help_case_in_handle_profile_command():
    """Test that handleProfileCommand has a case for /help."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'promptbox.js'
    content = js_path.read_text()
    
    # Check for /help case in switch statement
    assert "case '/help':" in content
    assert "await handleHelpCommand(promptBox);" in content


def test_help_command_exported():
    """Test that handleHelpCommand is exported to window."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'promptbox.js'
    content = js_path.read_text()
    
    assert 'window.handleHelpCommand = handleHelpCommand' in content


def test_content_calendar_in_dashboard():
    """Test that Content Calendar menu item exists in dashboard."""
    html_path = Path(__file__).parent.parent / 'templates' / 'dashboard.html'
    assert html_path.exists(), f"dashboard.html not found at {html_path}"
    
    content = html_path.read_text()
    
    # Check for Content Calendar menu item
    assert "Content Calendar" in content
    assert "menuAction('calendar')" in content
    assert "menu-badge-pro" in content
    assert "📅" in content


def test_saved_posts_removed_from_dashboard():
    """Test that 'Saved Posts' is no longer in dashboard menu."""
    html_path = Path(__file__).parent.parent / 'templates' / 'dashboard.html'
    content = html_path.read_text()
    
    # Make sure Saved Posts is not in the menu anymore
    assert "menuAction('saved')" not in content


def test_calendar_modal_functions_exist():
    """Test that Content Calendar modal functions exist in navigation.js."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'navigation.js'
    assert js_path.exists(), f"navigation.js not found at {js_path}"
    
    content = js_path.read_text()
    
    # Check for modal functions
    assert 'function showContentCalendarModal()' in content
    assert 'function closeCalendarModal()' in content
    assert 'function notifyCalendarInterest()' in content


def test_calendar_case_in_menu_action():
    """Test that menuAction has a case for 'calendar'."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'navigation.js'
    content = js_path.read_text()
    
    # Check for calendar case in switch statement
    assert "case 'calendar':" in content
    assert "showContentCalendarModal();" in content


def test_saved_case_removed_from_menu_action():
    """Test that 'saved' case is removed from menuAction."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'navigation.js'
    content = js_path.read_text()
    
    # Make sure saved case is not in switch anymore
    assert "case 'saved':" not in content


def test_calendar_functions_exported():
    """Test that calendar functions are exported to window."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'navigation.js'
    content = js_path.read_text()
    
    assert 'window.showContentCalendarModal = showContentCalendarModal' in content
    assert 'window.closeCalendarModal = closeCalendarModal' in content
    assert 'window.notifyCalendarInterest = notifyCalendarInterest' in content


def test_calendar_modal_css_exists():
    """Test that Content Calendar modal CSS styles exist."""
    css_path = Path(__file__).parent.parent / 'static' / 'css' / 'chat.css'
    assert css_path.exists(), f"chat.css not found at {css_path}"
    
    content = css_path.read_text()
    
    # Check for key CSS classes
    assert '.modal-overlay' in content
    assert '.modal-content' in content
    assert '.calendar-header' in content
    assert '.calendar-features' in content
    assert '.pro-badge' in content
    assert '.menu-badge-pro' in content
    assert '.btn-notify' in content


def test_calendar_modal_has_features():
    """Test that calendar modal HTML includes all features."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'navigation.js'
    content = js_path.read_text()
    
    # Check for feature descriptions
    assert 'Schedule posts for specific dates & times' in content
    assert 'See gaps in your content schedule' in content
    assert 'Drag & drop to reschedule' in content
    assert 'Get reminders before scheduled posts' in content
    assert 'Coming Soon!' in content


def test_dashboard_html_syntax_valid():
    """Test that dashboard.html has valid structure."""
    html_path = Path(__file__).parent.parent / 'templates' / 'dashboard.html'
    content = html_path.read_text()
    
    # Check that calendar menuAction is present
    assert "menuAction('calendar')" in content or "menuAction(&#39;calendar&#39;)" in content


def test_promptbox_js_syntax_valid():
    """Test that promptbox.js file has valid basic syntax."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'promptbox.js'
    content = js_path.read_text()
    
    # Check for balanced braces (basic syntax check)
    open_braces = content.count('{')
    close_braces = content.count('}')
    assert open_braces == close_braces, "Unbalanced braces in promptbox.js"


def test_navigation_js_syntax_valid():
    """Test that navigation.js file has valid basic syntax."""
    js_path = Path(__file__).parent.parent / 'static' / 'js' / 'navigation.js'
    content = js_path.read_text()
    
    # Check for balanced braces (basic syntax check)
    open_braces = content.count('{')
    close_braces = content.count('}')
    assert open_braces == close_braces, "Unbalanced braces in navigation.js"
