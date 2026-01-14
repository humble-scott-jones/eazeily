"""Simple integration test to demonstrate profile data flows through generation."""
import pytest
from unittest.mock import Mock, patch


def test_voice_engine_prompt_includes_profile_data():
    """Demonstrate that VoiceEngine builds prompts with profile data."""
    from services.voice_engine import VoiceEngine
    
    # Create a profile with comprehensive data
    class RealProfile:
        industry = 'Technology'
        business_name = 'TechCorp'
        brand_voice = 'Innovative and bold'
        target_audience = 'Tech executives'
        key_offer = 'AI automation solutions'
        voice_rules = 'No jargon, always mention ROI'
        
        def get_writing_samples(self):
            return ['We help companies scale through AI automation.']
        
        def get_brand_keywords(self):
            return ['AI', 'automation', 'efficiency']
        
        def get_niche_keywords(self):
            return ['machine learning', 'cloud computing']
        
        def get_customers(self):
            return ['Enterprise', 'Fortune 500']
        
        def get_scraped_meta(self):
            return {'key_customers': 'Tech companies'}
    
    profile = RealProfile()
    engine = VoiceEngine()
    
    # Mock the model to capture the prompt
    mock_response = Mock()
    mock_response.text = 'Generated content'
    
    captured_prompts = []
    
    def capture_prompt(prompt):
        captured_prompts.append(prompt)
        return mock_response
    
    engine.model = Mock()
    engine.model.generate_content = capture_prompt
    
    # Generate content
    result = engine.generate_expert_content(
        profile,
        'How to scale your business with AI',
        'post',
        'linkedin'
    )
    
    # Verify result
    assert result == 'Generated content'
    assert len(captured_prompts) == 1
    
    # Verify prompt includes profile data
    prompt = captured_prompts[0]
    print("\n=== GENERATED PROMPT ===")
    print(prompt)
    print("=== END PROMPT ===\n")
    
    # Check all profile data is in the prompt
    assert 'TechCorp' in prompt
    assert 'Technology' in prompt
    assert 'Innovative and bold' in prompt
    assert 'Tech executives' in prompt
    assert 'AI automation solutions' in prompt
    assert 'No jargon' in prompt or 'ROI' in prompt
    assert 'AI' in prompt or 'automation' in prompt
    assert 'machine learning' in prompt or 'cloud computing' in prompt
    assert 'Enterprise' in prompt or 'Fortune 500' in prompt
    assert 'scale through AI automation' in prompt
    

def test_dummy_profile_generates_content_without_errors():
    """Demonstrate that dummy profile works for users without a profile."""
    from routes.generate_routes import _build_dummy_profile
    from services.voice_engine import VoiceEngine
    
    dummy_profile = _build_dummy_profile()
    engine = VoiceEngine()
    
    # Mock the model
    mock_response = Mock()
    mock_response.text = 'Fallback generated content'
    engine.model = Mock()
    engine.model.generate_content = Mock(return_value=mock_response)
    
    # Should not raise AttributeError
    result = engine.generate_expert_content(
        dummy_profile,
        'Marketing tips for businesses',
        'post',
        'instagram'
    )
    
    assert result == 'Fallback generated content'
    assert engine.model.generate_content.called
    
    # Verify the prompt was built (even with dummy data)
    call_args = engine.model.generate_content.call_args
    prompt = call_args[0][0]
    
    # Should include dummy profile defaults
    assert 'Your Business' in prompt or 'general' in prompt.lower()


def test_profile_with_empty_optional_fields_works():
    """Test that profile with some empty optional fields still works."""
    from services.voice_engine import VoiceEngine
    
    class MinimalProfile:
        industry = 'Consulting'
        business_name = 'Acme Corp'
        brand_voice = 'Professional'
        target_audience = ''  # Empty
        key_offer = ''  # Empty
        voice_rules = ''  # Empty
        
        def get_writing_samples(self):
            return []  # Empty
        
        def get_brand_keywords(self):
            return []  # Empty
        
        def get_niche_keywords(self):
            return []  # Empty
        
        def get_customers(self):
            return []  # Empty
        
        def get_scraped_meta(self):
            return {}  # Empty
    
    profile = MinimalProfile()
    engine = VoiceEngine()
    
    # Mock model
    mock_response = Mock()
    mock_response.text = 'Content generated despite minimal profile'
    engine.model = Mock()
    engine.model.generate_content = Mock(return_value=mock_response)
    
    # Should still work
    result = engine.generate_expert_content(
        profile,
        'Business consulting best practices',
        'post',
        'linkedin'
    )
    
    assert result == 'Content generated despite minimal profile'
    assert engine.model.generate_content.called
    
    # Verify prompt was built with at least the core fields
    call_args = engine.model.generate_content.call_args
    prompt = call_args[0][0]
    assert 'Acme Corp' in prompt
    assert 'Consulting' in prompt
    assert 'Professional' in prompt
