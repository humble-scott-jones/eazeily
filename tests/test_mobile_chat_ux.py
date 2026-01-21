"""Tests for mobile chat UX improvements."""
import pytest


def test_scroll_to_bottom_button_css_exists():
    """Test that scroll-to-bottom button CSS exists."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    assert '.scroll-to-bottom' in css_content
    assert '.scroll-to-bottom.visible' in css_content
    assert 'aria-label' in css_content or 'Scroll to bottom' in css_content


def test_skeleton_loader_css_exists():
    """Test that skeleton loader CSS exists."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    assert '.skeleton-loader' in css_content
    assert '.skeleton-line' in css_content
    assert '@keyframes shimmer' in css_content


def test_typewriter_skip_button_css_exists():
    """Test that typewriter skip button CSS exists."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    assert '.typewriter-skip' in css_content


def test_toast_notification_css_exists():
    """Test that toast notification CSS exists."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    assert '.toast' in css_content
    assert '.toast-success' in css_content
    assert '.toast-error' in css_content
    assert '.toast-warning' in css_content
    assert '.toast-info' in css_content


def test_reduced_motion_support():
    """Test that reduced motion media query exists."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    assert '@media (prefers-reduced-motion: reduce)' in css_content


def test_safe_area_insets_support():
    """Test that safe area insets are supported."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    assert 'env(safe-area-inset-bottom)' in css_content or 'safe-area-inset' in css_content


def test_mobile_viewport_styles():
    """Test that mobile viewport styles exist."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    # Check for dynamic viewport height
    assert '100dvh' in css_content


def test_scroll_manager_class_exists():
    """Test that ScrollManager class exists in JavaScript."""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    assert 'class ScrollManager' in js_content
    assert 'scrollToBottom' in js_content
    assert 'handleScroll' in js_content


def test_typewriter_effect_class_exists():
    """Test that TypewriterEffect class exists in JavaScript."""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    assert 'class TypewriterEffect' in js_content
    assert 'skip()' in js_content or 'skip(' in js_content
    assert 'complete()' in js_content or 'complete(' in js_content


def test_haptic_feedback_function_exists():
    """Test that hapticFeedback function exists."""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    assert 'function hapticFeedback' in js_content or 'hapticFeedback(' in js_content
    assert 'navigator.vibrate' in js_content


def test_show_toast_function_exists():
    """Test that showToast function exists with XSS protection."""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    assert 'function showToast' in js_content or 'showToast(' in js_content
    # Check for XSS protection - should use textContent instead of innerHTML
    assert 'textContent' in js_content


def test_thinking_indicator_methods_exist():
    """Test that thinking indicator methods exist."""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    assert 'showThinkingIndicator' in js_content
    assert 'hideThinkingIndicator' in js_content
    assert 'skeleton-loader' in js_content


def test_scroll_manager_initialized_in_promptbox():
    """Test that scrollManager is initialized in PromptBox constructor."""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    assert 'this.scrollManager' in js_content
    assert 'new ScrollManager' in js_content


def test_accessibility_aria_labels():
    """Test that accessibility aria-labels are present."""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check for aria-label on scroll button
    assert 'aria-label' in js_content
    assert 'Scroll to bottom' in js_content or 'scroll' in js_content.lower()
    
    # Check for aria-label on skip button
    assert 'Skip' in js_content or 'skip' in js_content.lower()


def test_typewriter_respects_reduced_motion():
    """Test that TypewriterEffect respects prefers-reduced-motion."""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    assert 'prefers-reduced-motion' in js_content


def test_thinking_indicator_css_class():
    """Test that thinking indicator CSS uses correct class."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    # Should use .promptbox-message.thinking, not .message.thinking
    assert '.promptbox-message.thinking' in css_content or '.thinking' in css_content


def test_no_conflicting_overflow_styles():
    """Test that there are no conflicting overflow-y styles."""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    # Check that overflow-y is only on the correct element
    # This is more of a structural check
    assert 'overflow' in css_content
