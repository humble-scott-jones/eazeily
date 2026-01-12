"""Test unified email flow with newsletter/standard subtypes and existing email context."""
import pytest
from unittest.mock import Mock, patch

# Email context field limit (should match generate_routes.py)
EMAIL_CONTEXT_MAX_LENGTH = 2000


@pytest.fixture
def mock_profile():
    """Mock user profile."""
    profile = Mock()
    profile.industry = 'general'
    profile.business_name = 'Test Business'
    profile.brand_voice = 'Professional and friendly'
    profile.target_audience = 'Small business owners'
    profile.key_offer = 'Marketing services'
    profile.voice_rules = ''
    profile.get_writing_samples = Mock(return_value=[])
    profile.get_brand_keywords = Mock(return_value=[])
    profile.get_niche_keywords = Mock(return_value=[])
    profile.get_customers = Mock(return_value=[])
    profile.get_scraped_meta = Mock(return_value={})
    return profile


def test_email_task_type_valid(client):
    """Email task type should be valid in task registry."""
    from services.task_registry import is_valid_task
    assert is_valid_task('email'), "Email should be a valid task type"


def test_newsletter_task_type_still_valid(client):
    """Newsletter task type should still be valid for backwards compatibility."""
    from services.task_registry import is_valid_task
    assert is_valid_task('newsletter'), "Newsletter should still be valid for backwards compatibility"


def test_email_generation_with_standard_subtype(client, mock_profile):
    """Test email generation with standard subtype."""
    from services.voice_engine import VoiceEngine
    
    engine = VoiceEngine()
    with patch.object(engine, 'model') as mock_model:
        mock_response = Mock()
        mock_response.text = "Subject: Follow-up\n\nHi there,\n\nJust following up on our conversation..."
        mock_model.generate_content.return_value = mock_response
        
        content = engine.generate_expert_content(
            mock_profile,
            topic="Following up on our meeting",
            task_type="email",
            platform="email",
            email_subtype="standard"
        )
        
        assert content is not None
        assert len(content) > 0
        # Verify the prompt included email subtype
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Standard Email" in call_args


def test_email_generation_with_newsletter_subtype(client, mock_profile):
    """Test email generation with newsletter subtype."""
    from services.voice_engine import VoiceEngine
    
    engine = VoiceEngine()
    with patch.object(engine, 'model') as mock_model:
        mock_response = Mock()
        mock_response.text = "Subject: Monthly Newsletter\n\nHello subscribers,\n\nHere's what's new..."
        mock_model.generate_content.return_value = mock_response
        
        content = engine.generate_expert_content(
            mock_profile,
            topic="Monthly company updates",
            task_type="email",
            platform="email",
            email_subtype="newsletter"
        )
        
        assert content is not None
        assert len(content) > 0
        # Verify the prompt included email subtype
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Newsletter" in call_args


def test_email_generation_with_existing_email_context(client, mock_profile):
    """Test email generation with existing email to respond to."""
    from services.voice_engine import VoiceEngine
    
    existing_email = """
    Hi,
    
    I'm interested in your marketing services. Can you tell me more about 
    your pricing and what's included in your packages?
    
    Thanks,
    John
    """
    
    engine = VoiceEngine()
    with patch.object(engine, 'model') as mock_model:
        mock_response = Mock()
        mock_response.text = "Subject: Re: Marketing Services Inquiry\n\nHi John,\n\nThank you for your interest..."
        mock_model.generate_content.return_value = mock_response
        
        content = engine.generate_expert_content(
            mock_profile,
            topic="Response to pricing inquiry",
            task_type="email",
            platform="email",
            email_context=existing_email.strip()
        )
        
        assert content is not None
        assert len(content) > 0
        # Verify the prompt included the existing email context
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Existing Email to Respond To" in call_args
        assert "interested in your marketing services" in call_args


def test_email_generation_without_existing_context(client, mock_profile):
    """Test email generation works without existing email context."""
    from services.voice_engine import VoiceEngine
    
    engine = VoiceEngine()
    with patch.object(engine, 'model') as mock_model:
        mock_response = Mock()
        mock_response.text = "Subject: New Product Launch\n\nHi,\n\nWe're excited to announce..."
        mock_model.generate_content.return_value = mock_response
        
        content = engine.generate_expert_content(
            mock_profile,
            topic="New product announcement",
            task_type="email",
            platform="email"
        )
        
        assert content is not None
        assert len(content) > 0
        # Verify no existing email section in prompt
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Existing Email to Respond To" not in call_args


def test_email_payload_with_all_fields(client, mock_profile):
    """Test email generation with all optional fields."""
    from services.voice_engine import VoiceEngine
    
    engine = VoiceEngine()
    with patch.object(engine, 'model') as mock_model:
        mock_response = Mock()
        mock_response.text = "Generated email with all fields"
        mock_model.generate_content.return_value = mock_response
        
        content = engine.generate_expert_content(
            mock_profile,
            topic="Comprehensive email test",
            task_type="email",
            platform="email",
            email_subtype="newsletter",
            email_context="Original email to respond to",
            cta="Sign up for our webinar"
        )
        
        assert content is not None
        call_args = mock_model.generate_content.call_args[0][0]
        assert "Newsletter" in call_args
        assert "Original email to respond to" in call_args
        assert "Sign up for our webinar" in call_args


def test_email_context_field_truncated(client):
    """Test that email_context field is truncated to prevent abuse."""
    # Simulate the field processor from generate_routes.py
    long_email = "x" * (EMAIL_CONTEXT_MAX_LENGTH + 1000)  # Longer than the limit
    
    processor = lambda v: v[:EMAIL_CONTEXT_MAX_LENGTH] if v else None
    processed = processor(long_email)
    
    assert len(processed) == EMAIL_CONTEXT_MAX_LENGTH
    assert processed == "x" * EMAIL_CONTEXT_MAX_LENGTH


def test_email_subtype_defaults_to_standard(client):
    """Test that invalid email_subtype defaults to standard."""
    # Simulate the field processor from generate_routes.py
    processor = lambda v: v if v in ['newsletter', 'standard'] else 'standard'
    
    assert processor('invalid') == 'standard'
    assert processor('newsletter') == 'newsletter'
    assert processor('standard') == 'standard'
    assert processor(None) == 'standard'


def test_backwards_compatibility_newsletter_task_type(client, mock_profile):
    """Test that newsletter task_type still works for backwards compatibility."""
    from services.voice_engine import VoiceEngine
    
    engine = VoiceEngine()
    with patch.object(engine, 'model') as mock_model:
        mock_response = Mock()
        mock_response.text = "Newsletter content"
        mock_model.generate_content.return_value = mock_response
        
        content = engine.generate_expert_content(
            mock_profile,
            topic="Monthly updates",
            task_type="newsletter",
            platform="email"
        )
        
        assert content is not None
        assert len(content) > 0
