"""
Test PromptBox markdown rendering functionality
"""
import re
from pathlib import Path


def test_rendermarkdown_has_header_support():
    """Verify renderMarkdown() function handles markdown headers"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check for h2 header rendering (## text)
    assert re.search(r"replace\([^)]*\^##\s", content), \
        "renderMarkdown() should support ## headers (h2)"
    
    # Check for h3 header rendering (### text)
    assert re.search(r"replace\([^)]*\^###\s", content), \
        "renderMarkdown() should support ### headers (h3)"
    
    # Check for h4 header rendering (#### text)
    assert re.search(r"replace\([^)]*\^####\s", content), \
        "renderMarkdown() should support #### headers (h4)"


def test_rendermarkdown_has_horizontal_rule_support():
    """Verify renderMarkdown() function handles horizontal rules"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Check for horizontal rule rendering (---)
    assert re.search(r"replace\([^)]*\^---\$", content), \
        "renderMarkdown() should support --- horizontal rules"


def test_rendermarkdown_processes_headers_before_bold():
    """Verify headers are processed before bold to avoid conflicts"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Extract the renderMarkdown function
    match = re.search(r"renderMarkdown\(text\)\s*{(.+?)^\s*}", content, re.DOTALL | re.MULTILINE)
    assert match, "Could not find renderMarkdown function"
    
    function_body = match.group(1)
    
    # Find positions of header and bold processing
    header_pos = function_body.find("^##")
    bold_pos = function_body.find("**")
    
    assert header_pos > 0, "Headers should be processed in renderMarkdown"
    assert bold_pos > 0, "Bold should be processed in renderMarkdown"
    assert header_pos < bold_pos, \
        "Headers must be processed before bold to avoid conflicts with ## **text**"


def test_css_has_header_styles():
    """Verify CSS file has styling for markdown headers"""
    promptbox_css = Path("static/css/promptbox.css")
    content = promptbox_css.read_text()
    
    # Check for h2, h3, h4 styles
    assert ".promptbox-bubble h2" in content, \
        "CSS should have styles for h2 headers"
    assert ".promptbox-bubble h3" in content, \
        "CSS should have styles for h3 headers"
    assert ".promptbox-bubble h4" in content, \
        "CSS should have styles for h4 headers"


def test_css_has_horizontal_rule_style():
    """Verify CSS file has styling for horizontal rules"""
    promptbox_css = Path("static/css/promptbox.css")
    content = promptbox_css.read_text()
    
    # Check for hr style
    assert ".promptbox-bubble hr" in content, \
        "CSS should have styles for horizontal rules"


def test_rendermarkdown_comment_mentions_headers():
    """Verify renderMarkdown comment is updated to mention headers"""
    promptbox_js = Path("static/js/promptbox.js")
    content = promptbox_js.read_text()
    
    # Find the renderMarkdown function
    match = re.search(r"renderMarkdown\(text\)\s*{(.{0,200})", content, re.DOTALL)
    assert match, "Could not find renderMarkdown function"
    
    # Check first comment inside function
    function_start = match.group(1)
    
    # Check that comment mentions headers or hr
    assert "header" in function_start.lower() or "hr" in function_start.lower(), \
        "renderMarkdown comment should mention headers or hr support"
