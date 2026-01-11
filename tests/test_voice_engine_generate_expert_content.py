"""Test the generate_expert_content method in voice_engine."""
import pytest
from services.voice_engine import VoiceEngine


class MockProfile:
    """Mock user profile for testing."""
    industry = "Technology"
    business_name = "Test Business"
    brand_voice = "Professional and friendly"


def test_generate_expert_content_returns_content():
    """Test that generate_expert_content returns content."""
    engine = VoiceEngine()
    
    # Test without actual API call (model will be None in test environment)
    profile = MockProfile()
    content = engine.generate_expert_content(
        profile,
        "How to use AI in business",
        "post",
        "LinkedIn"
    )
    
    # Should return a string (even if fallback)
    assert isinstance(content, str)
    assert len(content) > 0
    assert "post" in content.lower()


def test_generate_expert_content_handles_missing_model():
    """Test that it gracefully handles missing model."""
    engine = VoiceEngine()
    engine.model = None  # Explicitly set to None
    
    profile = MockProfile()
    content = engine.generate_expert_content(
        profile,
        "Test topic",
        "email",
        "LinkedIn"
    )
    
    # Should return fallback content
    assert isinstance(content, str)
    assert "email" in content


def test_generate_expert_content_accepts_all_parameters():
    """Test that all parameters are accepted without errors."""
    engine = VoiceEngine()
    profile = MockProfile()
    
    # Test with different task types and platforms
    for task_type in ["post", "email", "script", "caption"]:
        for platform in ["LinkedIn", "Instagram", "Facebook", "Twitter"]:
            content = engine.generate_expert_content(
                profile,
                "Test topic",
                task_type,
                platform
            )
            assert isinstance(content, str)
            assert len(content) > 0


def test_generate_expert_content_with_minimal_profile():
    """Test with a profile that has minimal attributes."""
    class MinimalProfile:
        pass
    
    engine = VoiceEngine()
    profile = MinimalProfile()
    
    # Should not raise an error
    content = engine.generate_expert_content(
        profile,
        "Test topic",
        "post",
        "LinkedIn"
    )
    
    assert isinstance(content, str)
    assert len(content) > 0
