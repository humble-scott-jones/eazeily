"""
Test mobile chat UX improvements - CSS and JS features
"""


def test_chat_css_has_mobile_styles():
    """Verify chat.css contains mobile-optimized styles"""
    with open('static/css/chat.css', 'r') as f:
        css_content = f.read()
    
    # Check for mobile viewport styles
    assert '100dvh' in css_content, "Missing dynamic viewport height"
    assert '-webkit-overflow-scrolling: touch' in css_content, "Missing touch scrolling"
    
    # Check for scroll-to-bottom button
    assert '.scroll-to-bottom' in css_content, "Missing scroll-to-bottom button styles"
    assert '.scroll-to-bottom.visible' in css_content, "Missing visible state"
    assert '.scroll-to-bottom.has-new' in css_content, "Missing new message indicator"
    
    # Check for skeleton loader
    assert '.skeleton-loader' in css_content, "Missing skeleton loader"
    assert '.skeleton-line' in css_content, "Missing skeleton lines"
    assert '@keyframes shimmer' in css_content, "Missing shimmer animation"
    
    # Check for typewriter skip button
    assert '.typewriter-skip' in css_content, "Missing typewriter skip button"
    
    # Check for toast notifications
    assert '.toast' in css_content, "Missing toast notification styles"
    assert '.toast-success' in css_content, "Missing success toast"
    assert '.toast-error' in css_content, "Missing error toast"
    
    # Check for reduced motion support
    assert '@media (prefers-reduced-motion: reduce)' in css_content, "Missing reduced motion support"
    
    # Check for mobile media queries
    assert '@media (max-width: 640px)' in css_content, "Missing mobile media queries"
    assert 'env(safe-area-inset-bottom)' in css_content, "Missing safe area insets"


def test_promptbox_has_scroll_manager():
    """Verify promptbox.js contains ScrollManager class"""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check for ScrollManager class
    assert 'class ScrollManager' in js_content, "Missing ScrollManager class"
    assert 'onNewMessage()' in js_content, "Missing onNewMessage method"
    assert 'scrollToBottom' in js_content, "Missing scrollToBottom method"
    assert 'handleScroll' in js_content, "Missing handleScroll method"
    assert 'isUserScrolledUp' in js_content, "Missing scroll state tracking"


def test_promptbox_has_typewriter_effect():
    """Verify promptbox.js contains TypewriterEffect class"""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check for TypewriterEffect class
    assert 'class TypewriterEffect' in js_content, "Missing TypewriterEffect class"
    assert 'prefersReducedMotion' in js_content, "Missing reduced motion check"
    assert 'skipButton' in js_content, "Missing skip button"
    assert 'skip()' in js_content, "Missing skip method"
    assert 'chunkSize' in js_content, "Missing chunk-based typing"


def test_promptbox_has_skeleton_loader():
    """Verify promptbox.js contains skeleton loader methods"""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check for skeleton loader methods
    assert 'showThinkingIndicator()' in js_content, "Missing showThinkingIndicator method"
    assert 'hideThinkingIndicator()' in js_content, "Missing hideThinkingIndicator method"
    assert 'skeleton-loader' in js_content, "Missing skeleton-loader reference"
    assert 'thinking-text' in js_content, "Missing thinking text"


def test_promptbox_has_haptic_feedback():
    """Verify promptbox.js contains haptic feedback"""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check for haptic feedback function
    assert 'function hapticFeedback' in js_content, "Missing hapticFeedback function"
    assert 'navigator.vibrate' in js_content, "Missing vibration API check"
    assert 'patterns' in js_content, "Missing vibration patterns"


def test_promptbox_has_toast_notifications():
    """Verify promptbox.js contains toast notification system"""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check for toast functions
    assert 'function showToast' in js_content, "Missing showToast function"
    assert 'function getToastIcon' in js_content, "Missing getToastIcon function"
    # Check for toast class references
    assert "'success'" in js_content or '"success"' in js_content, "Missing success toast reference"
    assert "'error'" in js_content or '"error"' in js_content, "Missing error toast reference"


def test_promptbox_integrates_scroll_manager():
    """Verify PromptBox integrates ScrollManager"""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check for ScrollManager integration
    assert 'this.scrollManager = null' in js_content, "Missing scrollManager property"
    assert 'initScrollManager' in js_content, "Missing initScrollManager method"
    assert 'this.scrollManager?.onNewMessage()' in js_content, "Missing scrollManager usage"


def test_copy_uses_haptic_and_toast():
    """Verify copy functionality uses haptic feedback and toast"""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check that copyContent uses hapticFeedback and showToast
    assert "hapticFeedback('success')" in js_content, "Missing haptic feedback on copy"
    assert "showToast('Copied!', 'success')" in js_content, "Missing toast on copy"


def test_exports_new_classes():
    """Verify new classes and functions are exported"""
    with open('static/js/promptbox.js', 'r') as f:
        js_content = f.read()
    
    # Check exports - look for them anywhere in the file
    assert 'window.ScrollManager = ScrollManager' in js_content, "ScrollManager not exported"
    assert 'window.TypewriterEffect = TypewriterEffect' in js_content, "TypewriterEffect not exported"
    assert 'window.hapticFeedback = hapticFeedback' in js_content, "hapticFeedback not exported"
    assert 'window.showToast = showToast' in js_content, "showToast not exported"
