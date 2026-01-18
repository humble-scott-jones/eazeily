"""
Test chat UI fixes for button click handlers and input clearance
"""
from pathlib import Path


def test_chat_css_has_sufficient_padding_for_buttons():
    """Verify chat-messages has adequate padding-bottom for input + buttons"""
    chat_css = Path("static/css/chat.css")
    content = chat_css.read_text()
    
    # Find the .chat-messages class and verify padding-bottom
    import re
    pattern = r'\.chat-messages\s*\{[^}]*padding-bottom:\s*(\d+)px'
    match = re.search(pattern, content)
    
    assert match, "Could not find .chat-messages padding-bottom"
    padding = int(match.group(1))
    assert padding >= 140, f"padding-bottom should be at least 140px for button clearance, got {padding}px"


def test_promptbox_button_handler_checks_embedded_mode():
    """Verify renderMessageButtons() uses correct textarea ID for embedded mode"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check that button handlers use conditional logic for embedded mode
    assert "const textareaId = this.embedded ? 'chat-input'" in content, \
        "Button handler should use 'chat-input' ID when embedded"
    assert "const sendBtnId = this.embedded ? 'send-btn'" in content, \
        "Button handler should use 'send-btn' ID when embedded"


def test_promptbox_button_handler_uses_correct_autoresize():
    """Verify button handler uses correct autoResize function for embedded mode"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check for conditional autoResize logic
    assert "if (this.embedded && typeof autoResizeTextarea === 'function')" in content, \
        "Should use global autoResizeTextarea function in embedded mode"
    assert "autoResizeTextarea(textarea);" in content, \
        "Should call global autoResizeTextarea in embedded mode"


def test_promptbox_button_handler_enables_send_button():
    """Verify button handler enables send button after pre-filling"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check that send button is enabled after prompt action
    # Simple check that the disable logic is present
    assert "sendBtn.disabled = false" in content, \
        "Button handler should enable send button after pre-filling textarea"


def test_promptbox_command_action_uses_sendmessage():
    """Verify command action uses sendMessage instead of handleSend"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check that command action uses sendMessage in renderMessageButtons
    assert "this.sendMessage(btn.value)" in content, \
        "Command action should use this.sendMessage() in button handlers"
