"""Test that generated captions never contain coaching language."""

from services.generation.output_validator import detect_coaching_phrases


def test_detect_coaching_phrases_finds_you_should():
    """Test that 'you should' is detected as coaching language."""
    text = "You should post this on Instagram for maximum engagement."
    detected = detect_coaching_phrases(text)
    assert detected is not None
    assert any('you should' in phrase.lower() for phrase in detected)


def test_detect_coaching_phrases_finds_consider():
    """Test that 'consider' is detected as coaching language in advisory context."""
    text = "Consider adding more emojis to make it pop."
    detected = detect_coaching_phrases(text)
    assert detected is not None
    # The pattern captures the action word after "consider", e.g., "adding"
    assert any(word in ['adding', 'posting', 'using', 'trying', 'including', 'making'] for word in detected)


def test_detect_coaching_phrases_allows_legitimate_consider():
    """Test that legitimate business use of 'consider' is not flagged."""
    legitimate_captions = [
        "We consider customer feedback the heart of our business.",
        "Consider us your trusted partner in growth.",
        "Many consider our service the best in the industry."
    ]
    
    for caption in legitimate_captions:
        detected = detect_coaching_phrases(caption)
        assert detected is None, f"False positive for legitimate 'consider': {caption}"


def test_detect_coaching_phrases_finds_try_to():
    """Test that 'try to' is detected as coaching language."""
    text = "Try to keep your captions under 150 characters."
    detected = detect_coaching_phrases(text)
    assert detected is not None
    assert any('try to' in phrase.lower() for phrase in detected)


def test_detect_coaching_phrases_finds_heres_what_to_say():
    """Test that 'here's what to say' is detected as coaching language."""
    text = "Here's what to say: We're excited to announce our new product!"
    detected = detect_coaching_phrases(text)
    assert detected is not None
    assert any('here\'s what to say' in phrase.lower() for phrase in detected)


def test_detect_coaching_phrases_finds_multiple():
    """Test detection of multiple coaching phrases in one text."""
    text = "You should consider posting this, and try to add hashtags."
    detected = detect_coaching_phrases(text)
    assert detected is not None
    assert len(detected) >= 3  # should find 'you should', 'consider', 'try to'


def test_detect_coaching_phrases_none_for_clean_text():
    """Test that clean, post-ready text has no coaching phrases."""
    text = "We're excited to announce our new product launch! 🎉 Check it out today."
    detected = detect_coaching_phrases(text)
    assert detected is None


def test_detect_coaching_phrases_none_for_action_verbs():
    """Test that normal action verbs don't trigger false positives."""
    text = "Join us for our grand opening. You'll love our new location!"
    detected = detect_coaching_phrases(text)
    assert detected is None


def test_action_verb_try_without_to_is_allowed():
    """Test that 'Try' as action verb (without 'to') is allowed in captions."""
    captions_with_try = [
        "Try our seasonal pumpkin spice latte this fall!",
        "Try it today and see the difference.",
        "New customers can try our service free for 30 days."
    ]
    
    for caption in captions_with_try:
        detected = detect_coaching_phrases(caption)
        assert detected is None, f"'Try' without 'to' should not be flagged: {caption}"


def test_detect_coaching_phrases_case_insensitive():
    """Test that detection works regardless of case."""
    text = "YOU SHOULD check this out. Consider posting THIS today."
    detected = detect_coaching_phrases(text)
    assert detected is not None
    assert len(detected) >= 2


def test_caption_examples_dont_have_coaching():
    """Test realistic post-ready captions don't contain coaching phrases."""
    captions = [
        "🌟 New menu alert! Taste our seasonal pumpkin spice latte this fall. Available now at all locations.",
        "Behind the scenes: Watch how we craft each artisan loaf by hand. Link in bio for the full video! 🍞",
        "Thank you @customer for this amazing review! We're so grateful for your support. 💙",
        "Big news dropping Friday at 9am PST. Set your reminders! 📱✨",
        "Your fitness journey starts here. Join our community today and transform your life. 💪"
    ]
    
    for caption in captions:
        detected = detect_coaching_phrases(caption)
        assert detected is None, f"False positive in caption: {caption}"


def test_coaching_phrases_in_notes_field_ok():
    """Test that strategy notes can contain coaching (they're separate from caption)."""
    # This is a documentation test - notes field is allowed to have coaching
    # because it's collapsed in UI and separate from the paste-ready caption
    notes = [
        "Consider posting this during peak engagement hours (6-9pm)",
        "You should tag your local business partners for reach"
    ]
    
    # Notes are allowed to have coaching language - they're strategy tips
    for note in notes:
        detected = detect_coaching_phrases(note)
        # We detect them, but they're in the notes field, not caption
        assert detected is not None


def test_banned_phrases_list_complete():
    """Test coverage of all banned coaching phrases."""
    banned_tests = [
        "you should post this",
        "consider adding hashtags",
        "consider posting during peak hours",
        "try to keep it short",
        "make sure to tag us",
        "don't forget to link",
        "remember to mention",
        "here's what to say",
        "here's how to frame it",
        "think about your audience",
        "feel free to customize",
        "you could add emojis",
        "you might want to shorten",
        "it's important to engage",
        "be sure to follow up"
    ]
    
    for text in banned_tests:
        detected = detect_coaching_phrases(text)
        assert detected is not None, f"Failed to detect coaching in: {text}"
