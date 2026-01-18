"""
Test PromptBox setLoading() method handles embedded mode properly
This test ensures the critical bug fix for embedded mode is working.
"""
import re
from pathlib import Path


def test_setloading_checks_embedded_mode():
    """Verify setLoading() checks embedded mode before DOM access"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find setLoading method
    setloading_match = re.search(
        r'setLoading\(isLoading\)\s*{(.*?)\n  }',
        content,
        re.DOTALL
    )
    assert setloading_match, "setLoading() method not found"
    
    method_body = setloading_match.group(1)
    
    # Check that it checks embedded mode early
    assert "if (this.embedded)" in method_body, \
        "setLoading() should check this.embedded flag"
    assert "return" in method_body, \
        "setLoading() should return early in embedded mode"


def test_setloading_has_optional_event_handler():
    """Verify setLoading() can optionally notify page of loading state"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find setLoading method
    setloading_match = re.search(
        r'setLoading\(isLoading\)\s*{(.*?)\n  }',
        content,
        re.DOTALL
    )
    assert setloading_match, "setLoading() method not found"
    
    method_body = setloading_match.group(1)
    
    # Check for optional window callback
    assert "window.handleLoadingStateChange" in method_body, \
        "setLoading() should support optional window.handleLoadingStateChange callback"


def test_setloading_has_null_checks():
    """Verify setLoading() has null checks for DOM elements"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find setLoading method
    setloading_match = re.search(
        r'setLoading\(isLoading\)\s*{(.*?)\n  }',
        content,
        re.DOTALL
    )
    assert setloading_match, "setLoading() method not found"
    
    method_body = setloading_match.group(1)
    
    # Check for null checks before accessing classList
    assert "if (loadingEl)" in method_body, \
        "setLoading() should check if loadingEl exists"
    assert "if (textarea)" in method_body, \
        "setLoading() should check if textarea exists"
    assert "if (sendBtn)" in method_body, \
        "setLoading() should check if sendBtn exists"


def test_autoresize_textarea_has_null_check():
    """Verify autoResizeTextarea() has null check"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find autoResizeTextarea method
    method_match = re.search(
        r'autoResizeTextarea\(textarea\)\s*{(.*?)^\s*}',
        content,
        re.DOTALL | re.MULTILINE
    )
    assert method_match, "autoResizeTextarea() method not found"
    
    method_body = method_match.group(1)
    
    # Check for null check at start
    lines = method_body.strip().split('\n')
    first_line = lines[0].strip()
    assert "if (!textarea) return" in first_line or "if (!textarea)" in first_line, \
        "autoResizeTextarea() should have null check as first line"


def test_update_send_button_has_null_check():
    """Verify updateSendButton() has null checks"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find updateSendButton method
    method_match = re.search(
        r'updateSendButton\(textarea,\s*sendBtn\)\s*{(.*?)^\s*}',
        content,
        re.DOTALL | re.MULTILINE
    )
    assert method_match, "updateSendButton() method not found"
    
    method_body = method_match.group(1)
    
    # Check for null checks at start
    lines = method_body.strip().split('\n')
    first_line = lines[0].strip()
    assert ("!textarea" in first_line and "!sendBtn" in first_line) or \
           ("if (!textarea || !sendBtn) return" in first_line), \
        "updateSendButton() should check both textarea and sendBtn for null"


def test_scroll_to_bottom_has_null_check():
    """Verify scrollToBottom() has null check"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find scrollToBottom method
    method_match = re.search(
        r'scrollToBottom\(\)\s*{(.*?)^\s*}',
        content,
        re.DOTALL | re.MULTILINE
    )
    assert method_match, "scrollToBottom() method not found"
    
    method_body = method_match.group(1)
    
    # Check for null check on conversation element
    assert "if (conversation)" in method_body, \
        "scrollToBottom() should check if conversation element exists"


def test_setloading_embedded_check_before_getelementbyid():
    """Verify embedded check happens BEFORE getElementById calls"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find setLoading method
    setloading_match = re.search(
        r'setLoading\(isLoading\)\s*{(.*?)\n  }',
        content,
        re.DOTALL
    )
    assert setloading_match, "setLoading() method not found"
    
    method_body = setloading_match.group(1)
    
    # Find positions of key elements
    embedded_check_pos = method_body.find("if (this.embedded)")
    getelementbyid_pos = method_body.find("document.getElementById")
    
    assert embedded_check_pos != -1, "Embedded check not found"
    assert getelementbyid_pos != -1, "getElementById call not found"
    assert embedded_check_pos < getelementbyid_pos, \
        "Embedded mode check must come BEFORE getElementById calls to prevent null access"
