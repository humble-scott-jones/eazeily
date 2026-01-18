"""
Integration test to verify setLoading() works correctly in embedded mode.
This simulates the real-world scenario where commands are executed.
"""
import re
from pathlib import Path


def test_embedded_mode_sendmessage_calls_setloading():
    """Verify sendMessage() calls setLoading() which won't crash in embedded mode"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find sendMessage method
    sendmessage_match = re.search(
        r'async sendMessage\(message\)\s*{(.*?)^\s*}',
        content,
        re.DOTALL | re.MULTILINE
    )
    assert sendmessage_match, "sendMessage() method not found"
    
    method_body = sendmessage_match.group(1)
    
    # Verify it calls setLoading
    assert "this.setLoading(true)" in method_body, \
        "sendMessage() should call setLoading(true)"
    assert "this.setLoading(false)" in method_body, \
        "sendMessage() should call setLoading(false)"


def test_handlesend_calls_setloading():
    """Verify handleSend() calls setLoading() which won't crash in embedded mode"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find handleSend method
    handlesend_match = re.search(
        r'async handleSend\(\)\s*{(.*?)^\s*}',
        content,
        re.DOTALL | re.MULTILINE
    )
    assert handlesend_match, "handleSend() method not found"
    
    method_body = handlesend_match.group(1)
    
    # Verify it calls setLoading
    assert "this.setLoading(true)" in method_body, \
        "handleSend() should call setLoading(true)"
    assert "this.setLoading(false)" in method_body, \
        "handleSend() should call setLoading(false)"


def test_promptbox_js_syntax_valid():
    """Verify promptbox.js has valid JavaScript syntax"""
    import subprocess
    import shutil
    
    node = shutil.which("node")
    if not node:
        import pytest
        pytest.skip("node not available")
    
    promptbox_js = Path("static/js/promptbox.js")
    result = subprocess.run(
        [node, "--check", str(promptbox_js)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, \
        f"promptbox.js has syntax errors: {result.stderr or result.stdout}"


def test_embedded_mode_blocks_input_rendering():
    """Verify embedded mode skips rendering input/textarea/send button"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find render method
    render_match = re.search(
        r'render\(\)\s*{(.*?)^\s*}',
        content,
        re.DOTALL | re.MULTILINE
    )
    assert render_match, "render() method not found"
    
    method_body = render_match.group(1)
    
    # Check embedded mode renders only messages, skips input area
    assert "if (this.embedded)" in method_body, \
        "render() should check embedded mode"
    assert "promptbox-messages" in method_body, \
        "render() should always render messages container"
    
    # Verify the embedded block returns early
    embedded_block = re.search(
        r'if \(this\.embedded\)\s*{(.*?)return;',
        method_body,
        re.DOTALL
    )
    assert embedded_block, \
        "Embedded mode should return early without rendering input area"


def test_dashboard_uses_embedded_mode_initialization():
    """Verify dashboard.html initializes PromptBox in embedded mode"""
    dashboard_html = Path("templates/dashboard.html")
    content = dashboard_html.read_text()
    
    # Check for PromptBox initialization with embedded: true
    promptbox_init = re.search(
        r'new PromptBox\([^)]+{([^}]+)}',
        content,
        re.DOTALL
    )
    assert promptbox_init, "PromptBox initialization not found in dashboard.html"
    
    init_options = promptbox_init.group(1)
    assert "embedded: true" in init_options, \
        "Dashboard should initialize PromptBox with embedded: true"


def test_dashboard_connects_page_input_to_promptbox():
    """Verify dashboard connects its own input to PromptBox via sendMessage"""
    dashboard_html = Path("templates/dashboard.html")
    content = dashboard_html.read_text()
    
    # Check that dashboard calls promptBox.sendMessage
    assert "promptBox.sendMessage" in content, \
        "Dashboard should call promptBox.sendMessage() to send messages"
    
    # Check for page-level input handling
    assert "handlePageChatSend" in content, \
        "Dashboard should have handlePageChatSend function"


def test_fix_prevents_original_crash_scenario():
    """
    Verify the fix prevents the original crash:
    "Cannot read properties of null (reading 'classList')"
    
    The original code tried to access loadingEl.classList without checking
    if loadingEl exists in embedded mode.
    """
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
    
    # The fix has two layers of protection:
    # 1. Early return in embedded mode (before getElementById)
    # 2. Null checks before accessing classList
    
    # Check layer 1: embedded mode early return
    embedded_check_pos = method_body.find("if (this.embedded)")
    return_pos = method_body.find("return")
    getelementbyid_pos = method_body.find("document.getElementById")
    
    assert embedded_check_pos != -1, "Missing embedded mode check"
    assert return_pos != -1, "Missing early return"
    assert getelementbyid_pos != -1, "Missing getElementById"
    assert embedded_check_pos < return_pos < getelementbyid_pos, \
        "Embedded check must return BEFORE getElementById to prevent crash"
    
    # Check layer 2: null checks before classList access
    classlist_accesses = re.findall(r'(\w+)\.classList\.(add|remove)', method_body)
    
    # For each classList access, there should be a null check
    for element_var, _ in classlist_accesses:
        # Check that element is checked before use
        null_check_pattern = f"if \\({element_var}\\)"
        assert re.search(null_check_pattern, method_body), \
            f"Missing null check for {element_var} before classList access"
