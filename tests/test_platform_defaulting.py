"""Tests for platform defaulting behavior in content generation.

This test suite verifies that:
1. Social content types (post, caption, ad, script) default to Instagram
2. Non-social content types (review, email, blog, proposal) do NOT default to any platform
3. The voice_engine handles None platform gracefully
"""

import pytest
from unittest.mock import Mock, patch


def test_review_does_not_default_to_instagram(authenticated_client):
    """Test that review responses do NOT default to Instagram platform."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Thank you for your feedback!"
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            # Call _generate_content_response directly
            result = chat_routes._generate_content_response(
                task_type='review',
                params={'topic': 'their software is garbage 1 star'},
                profile=profile
            )
        
        # Verify the voice_engine was called with platform=None (not 'instagram')
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] is None  # Should NOT be 'instagram'
        assert call_kwargs['task_type'] == 'review'


def test_email_does_not_default_to_instagram(authenticated_client):
    """Test that emails do NOT default to Instagram platform."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Subject: Great opportunity\n\nHi there..."
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            result = chat_routes._generate_content_response(
                task_type='email',
                params={'topic': 'new product announcement'},
                profile=profile
            )
        
        # Verify platform is None
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] is None


def test_blog_does_not_default_to_instagram(authenticated_client):
    """Test that blog posts do NOT default to Instagram platform."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "# How to succeed\n\nBlog content..."
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            result = chat_routes._generate_content_response(
                task_type='blog',
                params={'topic': 'how to succeed in business'},
                profile=profile
            )
        
        # Verify platform is None
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] is None


def test_proposal_does_not_default_to_instagram(authenticated_client):
    """Test that proposals do NOT default to Instagram platform."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Proposal for XYZ Company..."
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            result = chat_routes._generate_content_response(
                task_type='proposal',
                params={'topic': 'website redesign project'},
                profile=profile
            )
        
        # Verify platform is None
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] is None


def test_newsletter_does_not_default_to_instagram(authenticated_client):
    """Test that newsletters do NOT default to Instagram platform."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Monthly Newsletter..."
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            result = chat_routes._generate_content_response(
                task_type='newsletter',
                params={'topic': 'monthly company updates'},
                profile=profile
            )
        
        # Verify platform is None
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] is None


def test_post_defaults_to_instagram(authenticated_client):
    """Test that social posts DO default to Instagram when no platform specified."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Check out our new product! 🎉"
        
        # Simulate the conversation router collecting fields but platform is somehow missing
        # This tests the safety net in _generate_content_response
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        # Get the authenticated user's profile
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            # Call _generate_content_response directly with no platform
            result = chat_routes._generate_content_response(
                task_type='post',
                params={'topic': 'new product launch'},  # No platform key
                profile=profile
            )
        
        # Verify platform defaults to 'instagram'
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] == 'instagram'


def test_post_respects_explicit_platform(authenticated_client):
    """Test that social posts use the explicitly provided platform."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "LinkedIn professional post"
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            # Call _generate_content_response directly WITH platform specified
            result = chat_routes._generate_content_response(
                task_type='post',
                params={'topic': 'new product launch', 'platform': 'LinkedIn'},
                profile=profile
            )
        
        # Verify platform is LinkedIn (not instagram)
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] == 'LinkedIn'


def test_caption_defaults_to_instagram(authenticated_client):
    """Test that captions DO default to Instagram when no platform specified."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Beautiful sunset 🌅 #nature"
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            # Call _generate_content_response directly with no platform
            result = chat_routes._generate_content_response(
                task_type='caption',
                params={'topic': 'photo of sunset'},
                profile=profile
            )
        
        # Verify platform defaults to 'instagram'
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] == 'instagram'


def test_ad_defaults_to_instagram(authenticated_client):
    """Test that ads DO default to Instagram when no platform specified."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Get 50% off today!"
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            # Call _generate_content_response directly with no platform
            result = chat_routes._generate_content_response(
                task_type='ad',
                params={'topic': 'spring sale promotion'},
                profile=profile
            )
        
        # Verify platform defaults to 'instagram'
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] == 'instagram'


def test_script_defaults_to_instagram(authenticated_client):
    """Test that video scripts DO default to Instagram when no platform specified."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "[HOOK] Check this out..."
        
        from routes import chat_routes
        from models import VoiceProfile
        from app import create_app
        
        test_app = authenticated_client.application
        with test_app.app_context():
            profile = VoiceProfile.query.filter_by(user_id=1).first()
            
            # Call _generate_content_response directly with no platform
            result = chat_routes._generate_content_response(
                task_type='script',
                params={'topic': 'product demo', 'video_length': '30s'},
                profile=profile
            )
        
        # Verify platform defaults to 'instagram'
        mock_engine.generate_expert_content.assert_called_once()
        call_kwargs = mock_engine.generate_expert_content.call_args[1]
        assert call_kwargs['platform'] == 'instagram'


def test_format_generated_content_uses_correct_labels(authenticated_client):
    """Test that formatting uses appropriate task labels."""
    with patch('routes.chat_routes.voice_engine') as mock_engine:
        mock_engine.generate_expert_content.return_value = "Thank you for your feedback!"
        
        response = authenticated_client.post('/api/chat', json={
            'message': 'continue',
            'pending_task': {
                'task_type': 'review',
                'collected': {'topic': 'great service'},
                'flow': 'content'
            }
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Check the response uses "review response" label, not just "review"
        assert 'review response' in data['response']
        assert data['response'].startswith('⭐')


def test_voice_engine_handles_none_platform():
    """Test that VoiceEngine handles None platform gracefully."""
    from services.voice_engine import VoiceEngine
    from unittest.mock import MagicMock
    
    # Create a mock profile
    mock_profile = MagicMock()
    mock_profile.industry = "Technology"
    mock_profile.business_name = "Test Company"
    mock_profile.brand_voice = "Professional"
    mock_profile.target_audience = "Developers"
    mock_profile.key_offer = "Great software"
    mock_profile.voice_rules = ""
    mock_profile.get_writing_samples.return_value = []
    mock_profile.get_brand_keywords.return_value = []
    mock_profile.get_niche_keywords.return_value = []
    mock_profile.get_customers.return_value = []
    mock_profile.get_scraped_meta.return_value = {}
    
    engine = VoiceEngine()
    
    # Test with platform=None (should not raise error)
    try:
        result = engine.generate_expert_content(
            user_profile=mock_profile,
            topic="test review",
            task_type="review",
            platform=None
        )
        # Should return either generated content or fallback
        assert result is not None
        assert isinstance(result, str)
        # Should NOT mention platform in fallback
        if "Generated" in result:
            assert "for None" not in result
    except Exception as e:
        pytest.fail(f"VoiceEngine should handle None platform gracefully, but raised: {e}")
