"""Test that dummy profile has all required methods for VoiceEngine."""
import pytest
from routes.generate_routes import _build_dummy_profile


def test_dummy_profile_has_all_required_methods():
    """Test that dummy profile implements all methods expected by VoiceEngine."""
    profile = _build_dummy_profile()
    
    # Test basic attributes
    assert hasattr(profile, 'industry')
    assert hasattr(profile, 'business_name')
    assert hasattr(profile, 'target_audience')
    assert hasattr(profile, 'brand_voice')
    assert hasattr(profile, 'key_offer')
    assert hasattr(profile, 'voice_rules')
    
    # Test all getter methods that VoiceEngine expects
    assert hasattr(profile, 'get_writing_samples')
    assert hasattr(profile, 'get_brand_keywords')
    assert hasattr(profile, 'get_niche_keywords')
    assert hasattr(profile, 'get_customers')
    assert hasattr(profile, 'get_scraped_meta')
    assert hasattr(profile, 'get_defaults')
    assert hasattr(profile, 'get_examples')
    
    # Test that methods are callable and return appropriate types
    assert isinstance(profile.get_writing_samples(), list)
    assert isinstance(profile.get_brand_keywords(), list)
    assert isinstance(profile.get_niche_keywords(), list)
    assert isinstance(profile.get_customers(), list)
    assert isinstance(profile.get_scraped_meta(), dict)
    assert isinstance(profile.get_defaults(), dict)
    assert isinstance(profile.get_examples(), list)


def test_dummy_profile_works_with_voice_engine():
    """Test that dummy profile can be used with VoiceEngine without errors."""
    from services.voice_engine import VoiceEngine
    
    profile = _build_dummy_profile()
    engine = VoiceEngine()
    
    # Should not raise any AttributeError
    result = engine.generate_expert_content(
        profile,
        'Test topic',
        'post',
        'LinkedIn'
    )
    
    # Should return a string
    assert isinstance(result, str)
    assert len(result) > 0
