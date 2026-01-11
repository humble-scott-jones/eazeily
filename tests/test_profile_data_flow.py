"""Integration tests for content generation with profile data."""
import pytest
from unittest.mock import Mock, patch
from services.voice_engine import VoiceEngine


class MockProfile:
    """Mock profile with all relevant fields."""
    def __init__(self, **kwargs):
        self.business_name = kwargs.get('business_name', 'Test Company')
        self.industry = kwargs.get('industry', 'Tech')
        self.brand_voice = kwargs.get('brand_voice', 'Professional')
        self.target_audience = kwargs.get('target_audience', 'Developers')
        self.key_offer = kwargs.get('key_offer', 'Best tools')
        self.voice_rules = kwargs.get('voice_rules', '')
        self._writing_samples = kwargs.get('writing_samples', [])
        self._brand_keywords = kwargs.get('brand_keywords', ['innovative'])
        self._niche_keywords = kwargs.get('niche_keywords', ['API'])
        self._customers = kwargs.get('customers', ['Enterprise', 'SMB'])
        self._scraped_meta = kwargs.get('scraped_meta', {})
    
    def get_writing_samples(self):
        return self._writing_samples
    
    def get_brand_keywords(self):
        return self._brand_keywords
    
    def get_niche_keywords(self):
        return self._niche_keywords
    
    def get_customers(self):
        return self._customers
    
    def get_scraped_meta(self):
        return self._scraped_meta


class TestProfileDataFlow:
    """Test that profile data flows correctly through generation."""
    
    def test_voice_engine_includes_customers_in_prompt(self):
        """Test that customer data is included in prompts."""
        engine = VoiceEngine()
        
        profile = MockProfile(
            business_name='Test Co',
            customers=['Startups', 'Enterprise'],
            brand_keywords=['fast', 'reliable']
        )
        
        # Mock the model to capture the prompt
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = 'Generated content'
        mock_model.generate_content.return_value = mock_response
        engine.model = mock_model
        
        result = engine.generate_expert_content(
            profile,
            'New feature release',
            'post',
            'linkedin'
        )
        
        # Verify the prompt was built
        assert mock_model.generate_content.called
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        
        # Verify profile data is in prompt
        assert 'Test Co' in prompt
        assert 'Startups' in prompt or 'Enterprise' in prompt
        assert 'fast' in prompt or 'reliable' in prompt
    
    def test_voice_engine_includes_niche_keywords(self):
        """Test that niche keywords are included in prompts."""
        engine = VoiceEngine()
        
        profile = MockProfile(
            niche_keywords=['SaaS', 'API', 'cloud-native'],
            brand_keywords=['modern', 'scalable']
        )
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = 'Generated content'
        mock_model.generate_content.return_value = mock_response
        engine.model = mock_model
        
        result = engine.generate_expert_content(
            profile,
            'Product update',
            'post',
            'twitter'
        )
        
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        
        # Verify niche keywords section exists
        assert 'Niche Keywords' in prompt or 'Industry-specific terms' in prompt
        assert any(keyword in prompt for keyword in ['SaaS', 'API', 'cloud-native'])
    
    def test_voice_engine_includes_scraped_metadata(self):
        """Test that scraped metadata is included in prompts."""
        engine = VoiceEngine()
        
        profile = MockProfile(
            scraped_meta={
                'key_customers': 'Tech companies and startups',
                'business_name': 'Official Business Name Inc.'
            }
        )
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = 'Generated content'
        mock_model.generate_content.return_value = mock_response
        engine.model = mock_model
        
        result = engine.generate_expert_content(
            profile,
            'Company announcement',
            'post',
            'linkedin'
        )
        
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        
        # Verify scraped metadata is in prompt
        assert 'Tech companies and startups' in prompt or 'Official Business Name' in prompt
    
    def test_voice_engine_handles_proposal_context(self):
        """Test that proposal-specific context is handled correctly."""
        engine = VoiceEngine()
        
        profile = MockProfile()
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = 'Proposal content'
        mock_model.generate_content.return_value = mock_response
        engine.model = mock_model
        
        result = engine.generate_expert_content(
            profile,
            'Partnership proposal',
            'proposal',
            '',
            proposal_type='partnership',
            recipient='Tech Corp',
            key_benefits=['Benefit 1', 'Benefit 2'],
            budget_range='$10k-$50k'
        )
        
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        
        # Verify proposal context in prompt
        assert 'Proposal Type: partnership' in prompt
        assert 'Recipient: Tech Corp' in prompt
        assert 'Benefit 1' in prompt or 'Key Benefits' in prompt
        assert '$10k-$50k' in prompt or 'Budget Range' in prompt
    
    def test_voice_engine_handles_review_reply_context(self):
        """Test that review reply context is handled correctly."""
        engine = VoiceEngine()
        
        profile = MockProfile()
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = 'Review reply'
        mock_model.generate_content.return_value = mock_response
        engine.model = mock_model
        
        result = engine.generate_expert_content(
            profile,
            'Great product!',
            'review_reply',
            '',
            review_source='Google',
            star_rating='5',
            sentiment='positive',
            desired_tone='grateful'
        )
        
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        
        # Verify review reply context in prompt
        assert 'Review Platform: Google' in prompt
        assert 'Star Rating: 5' in prompt
        assert 'Sentiment: positive' in prompt
        assert 'Desired Tone: grateful' in prompt
    
    def test_voice_engine_handles_blog_post_context(self):
        """Test that blog post context is handled correctly."""
        engine = VoiceEngine()
        
        profile = MockProfile()
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = 'Blog post content'
        mock_model.generate_content.return_value = mock_response
        engine.model = mock_model
        
        result = engine.generate_expert_content(
            profile,
            'How to build a startup',
            'blog_post',
            '',
            post_type='how-to',
            desired_length='medium',
            audience='entrepreneurs',
            seo_keywords=['startup', 'business', 'growth']
        )
        
        call_args = mock_model.generate_content.call_args
        prompt = call_args[0][0]
        
        # Verify blog post context in prompt
        assert 'Blog Post Type: how-to' in prompt
        assert '750-1000 words' in prompt or 'Target Length' in prompt
        assert 'Target Audience: entrepreneurs' in prompt
        assert 'startup' in prompt or 'SEO Keywords' in prompt
    
    def test_voice_engine_handles_missing_optional_fields(self):
        """Test that engine handles missing optional profile fields gracefully."""
        engine = VoiceEngine()
        
        # Minimal profile
        profile = MockProfile(
            business_name='Minimal Co',
            brand_keywords=[],
            niche_keywords=[],
            customers=[],
            scraped_meta={}
        )
        
        mock_model = Mock()
        mock_response = Mock()
        mock_response.text = 'Generated content'
        mock_model.generate_content.return_value = mock_response
        engine.model = mock_model
        
        # Should not raise any errors
        result = engine.generate_expert_content(
            profile,
            'Test topic',
            'post',
            'instagram'
        )
        
        assert result == 'Generated content'
        assert mock_model.generate_content.called
    
    def test_voice_engine_error_handling_timeout(self):
        """Test that engine handles timeout errors appropriately."""
        engine = VoiceEngine()
        
        profile = MockProfile()
        
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception('timeout occurred')
        engine.model = mock_model
        
        result = engine.generate_expert_content(
            profile,
            'Test topic',
            'post',
            'linkedin'
        )
        
        assert 'Error' in result
        assert ('timeout' in result.lower() or 'timed out' in result.lower())
    
    def test_voice_engine_error_handling_rate_limit(self):
        """Test that engine handles rate limit errors appropriately."""
        engine = VoiceEngine()
        
        profile = MockProfile()
        
        mock_model = Mock()
        mock_model.generate_content.side_effect = Exception('Rate limit exceeded')
        engine.model = mock_model
        
        result = engine.generate_expert_content(
            profile,
            'Test topic',
            'post',
            'linkedin'
        )
        
        assert 'Error' in result
        assert 'rate limit' in result.lower()
