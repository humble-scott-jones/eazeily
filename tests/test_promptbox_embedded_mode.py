"""
Test PromptBox embedded mode functionality
"""
import re
from pathlib import Path


def test_promptbox_js_has_embedded_option():
    """Verify PromptBox has embedded mode option in constructor"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check for embedded option in constructor
    assert "this.embedded = options.embedded" in content, \
        "PromptBox should accept embedded option in constructor"


def test_promptbox_js_render_checks_embedded_mode():
    """Verify render() method checks embedded mode"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check that render() checks embedded mode
    assert "if (this.embedded)" in content, \
        "render() should check embedded mode"
    assert "promptbox-embedded" in content, \
        "render() should add promptbox-embedded class in embedded mode"


def test_promptbox_js_has_send_message_method():
    """Verify PromptBox has sendMessage method for external input"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check for sendMessage method
    assert "async sendMessage(message)" in content or "sendMessage(message)" in content, \
        "PromptBox should have sendMessage() method for external input"


def test_dashboard_html_initializes_embedded_mode():
    """Verify dashboard.html initializes PromptBox with embedded: true"""
    dashboard_html = Path("templates/dashboard.html")
    content = dashboard_html.read_text()
    
    # Check for embedded: true in PromptBox initialization
    assert "embedded: true" in content, \
        "dashboard.html should initialize PromptBox with embedded: true"


def test_dashboard_html_has_page_level_input():
    """Verify dashboard has page-level input controls"""
    dashboard_html = Path("templates/dashboard.html")
    content = dashboard_html.read_text()
    
    # Check for page-level input elements
    assert 'id="chat-input"' in content, \
        "dashboard.html should have page-level chat input"
    assert 'id="send-btn"' in content, \
        "dashboard.html should have page-level send button"
    assert 'id="autocomplete-container"' in content, \
        "dashboard.html should have page-level autocomplete container"


def test_dashboard_html_connects_input_to_promptbox():
    """Verify dashboard connects page input to PromptBox"""
    dashboard_html = Path("templates/dashboard.html")
    content = dashboard_html.read_text()
    
    # Check for input connection function
    assert "connectPageInputToPromptBox" in content, \
        "dashboard.html should have function to connect page input to PromptBox"
    assert "handlePageChatSend" in content, \
        "dashboard.html should handle sending from page input"


def test_promptbox_css_has_embedded_styles():
    """Verify promptbox.css has styles for embedded mode"""
    promptbox_css = Path("static/css/promptbox.css")
    content = promptbox_css.read_text()
    
    # Check for embedded mode styles
    assert ".promptbox-embedded" in content, \
        "promptbox.css should have .promptbox-embedded class"
    assert "display: none !important" in content, \
        "embedded mode should force hide input/suggestions with !important"


def test_chat_css_has_autocomplete_styles():
    """Verify chat.css has autocomplete container styles"""
    chat_css = Path("static/css/chat.css")
    content = chat_css.read_text()
    
    # Check for autocomplete styles
    assert ".autocomplete-container" in content, \
        "chat.css should have .autocomplete-container styles"
    assert ".autocomplete-item" in content, \
        "chat.css should have .autocomplete-item styles"
    assert ".slash-hint" in content, \
        "chat.css should have .slash-hint styles"


def test_dashboard_only_one_header():
    """Verify dashboard has only one header (not duplicate)"""
    dashboard_html = Path("templates/dashboard.html")
    content = dashboard_html.read_text()
    
    # Count app-header occurrences
    header_matches = re.findall(r'class="app-header"', content)
    assert len(header_matches) == 1, \
        f"dashboard.html should have exactly one app-header, found {len(header_matches)}"


def test_dashboard_only_one_input_container():
    """Verify dashboard has only one input container (not duplicate)"""
    dashboard_html = Path("templates/dashboard.html")
    content = dashboard_html.read_text()
    
    # Count input-container occurrences
    input_matches = re.findall(r'class="input-container"', content)
    assert len(input_matches) == 1, \
        f"dashboard.html should have exactly one input-container, found {len(input_matches)}"
