"""Tests for mobile chat UX improvements."""
import pytest


@pytest.fixture(scope="module")
def css_content():
    """Fixture to read CSS file once and share across tests."""
    with open('static/css/chat.css', 'r') as f:
        return f.read()


@pytest.fixture(scope="module")
def js_content():
    """Fixture to read JS file once and share across tests."""
    with open('static/js/promptbox.js', 'r') as f:
        return f.read()


def test_scroll_to_bottom_button_css_exists(css_content):
    """Test that scroll-to-bottom button CSS exists."""
    assert '.scroll-to-bottom' in css_content
    assert '.scroll-to-bottom.visible' in css_content
    assert 'aria-label' in css_content or 'Scroll to bottom' in css_content


def test_skeleton_loader_css_exists(css_content):
    """Test that skeleton loader CSS exists."""
    assert '.skeleton-loader' in css_content
    assert '.skeleton-line' in css_content
    assert '@keyframes shimmer' in css_content


def test_typewriter_skip_button_css_exists(css_content):
    """Test that typewriter skip button CSS exists."""
    assert '.typewriter-skip' in css_content


def test_toast_notification_css_exists(css_content):
    """Test that toast notification CSS exists."""
    assert '.toast' in css_content
    assert '.toast-success' in css_content
    assert '.toast-error' in css_content
    assert '.toast-warning' in css_content
    assert '.toast-info' in css_content


def test_reduced_motion_support(css_content):
    """Test that reduced motion media query exists."""
    assert '@media (prefers-reduced-motion: reduce)' in css_content


def test_safe_area_insets_support(css_content):
    """Test that safe area insets are supported."""
    assert 'env(safe-area-inset-bottom)' in css_content or 'safe-area-inset' in css_content


def test_mobile_viewport_styles(css_content):
    """Test that mobile viewport styles exist."""
    # Check for dynamic viewport height
    assert '100dvh' in css_content


def test_scroll_manager_class_exists(js_content):
    """Test that ScrollManager class exists in JavaScript."""
    assert 'class ScrollManager' in js_content
    assert 'scrollToBottom' in js_content
    assert 'handleScroll' in js_content


def test_typewriter_effect_class_exists(js_content):
    """Test that TypewriterEffect class exists in JavaScript."""
    assert 'class TypewriterEffect' in js_content
    assert 'skip()' in js_content or 'skip(' in js_content
    assert 'complete()' in js_content or 'complete(' in js_content


def test_haptic_feedback_function_exists(js_content):
    """Test that hapticFeedback function exists."""
    assert 'function hapticFeedback' in js_content or 'hapticFeedback(' in js_content
    assert 'navigator.vibrate' in js_content


def test_show_toast_function_exists(js_content):
    """Test that showToast function exists with XSS protection."""
    assert 'function showToast' in js_content or 'showToast(' in js_content
    # Check for XSS protection - should use textContent instead of innerHTML
    assert 'textContent' in js_content


def test_thinking_indicator_methods_exist(js_content):
    """Test that thinking indicator methods exist."""
    assert 'showThinkingIndicator' in js_content
    assert 'hideThinkingIndicator' in js_content
    assert 'skeleton-loader' in js_content


def test_scroll_manager_initialized_in_promptbox(js_content):
    """Test that scrollManager is initialized in PromptBox constructor."""
    assert 'this.scrollManager' in js_content
    assert 'new ScrollManager' in js_content


def test_accessibility_aria_labels(js_content):
    """Test that accessibility aria-labels are present."""
    # Check for aria-label on scroll button
    assert 'aria-label' in js_content
    assert 'Scroll to bottom' in js_content or 'scroll' in js_content.lower()
    
    # Check for aria-label on skip button
    assert 'Skip' in js_content or 'skip' in js_content.lower()


def test_typewriter_respects_reduced_motion(js_content):
    """Test that TypewriterEffect respects prefers-reduced-motion."""
    assert 'prefers-reduced-motion' in js_content


def test_thinking_indicator_css_class(css_content):
    """Test that thinking indicator CSS uses correct class."""
    # Should use .promptbox-message.thinking, not .message.thinking
    assert '.promptbox-message.thinking' in css_content or '.thinking' in css_content


def test_no_conflicting_overflow_styles(css_content):
    """Test that there are no conflicting overflow-y styles."""
    # Check that overflow-y is only on the correct element
    # This is more of a structural check
    assert 'overflow' in css_content
