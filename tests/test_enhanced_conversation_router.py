"""Tests for enhanced conversation router features."""

import pytest
from unittest.mock import Mock
from services.conversation_router import ConversationRouter, MOOD_KEYWORDS


class MockProfile:
    """Mock VoiceProfile for testing."""
    def __init__(self):
        self.business_name = 'Test Business'
        self.industry = 'restaurant'


class TestEnhancedConversationRouter:
    """Test suite for enhanced conversation router features."""
    
    @pytest.fixture
    def router(self):
        """Create a ConversationRouter instance."""
        return ConversationRouter()
    
    @pytest.fixture
    def mock_profile(self):
        """Create a mock profile."""
        return MockProfile()
    
    # Test mood/tone extraction
    def test_extract_mood_excited(self, router):
        """Test extracting 'excited' mood."""
        params = router._extract_params_from_text('excited Instagram post about our sale', 'post')
        assert params.get('mood') == 'excited'
        assert params.get('platform') == 'instagram'
    
    def test_extract_mood_professional(self, router):
        """Test extracting 'professional' mood."""
        params = router._extract_params_from_text('professional LinkedIn post about our services', 'post')
        assert params.get('mood') == 'professional'
        assert params.get('platform') == 'linkedin'
    
    def test_extract_mood_casual(self, router):
        """Test extracting 'casual' mood."""
        params = router._extract_params_from_text('casual post about weekend plans', 'post')
        assert params.get('mood') == 'casual'
    
    def test_extract_mood_urgent(self, router):
        """Test extracting 'urgent' mood."""
        params = router._extract_params_from_text('urgent announcement about limited time offer', 'post')
        assert params.get('mood') == 'urgent'
    
    def test_extract_mood_celebratory(self, router):
        """Test extracting 'celebratory' mood."""
        params = router._extract_params_from_text('celebratory post about our anniversary', 'post')
        assert params.get('mood') == 'celebratory'
    
    def test_extract_mood_informative(self, router):
        """Test extracting 'informative' mood."""
        params = router._extract_params_from_text('informative post with tips for beginners', 'post')
        assert params.get('mood') == 'informative'
    
    def test_extract_mood_funny(self, router):
        """Test extracting 'funny' mood."""
        params = router._extract_params_from_text('funny post about office life', 'post')
        assert params.get('mood') == 'funny'
    
    def test_extract_mood_inspiring(self, router):
        """Test extracting 'inspiring' mood."""
        params = router._extract_params_from_text('inspiring message for Monday motivation', 'post')
        assert params.get('mood') == 'inspiring'
    
    def test_extract_mood_multi_word_phrases(self, router):
        """Test extracting moods from multi-word phrases."""
        # Test "limited time" (urgent)
        params = router._extract_params_from_text('limited time offer on products', 'post')
        assert params.get('mood') == 'urgent'
        
        # Test "laid back" (casual)
        params = router._extract_params_from_text('laid back weekend vibes', 'post')
        assert params.get('mood') == 'casual'
        
        # Test "how to" (informative)
        params = router._extract_params_from_text('how to improve your fitness', 'post')
        assert params.get('mood') == 'informative'
    
    # Test CTA extraction
    def test_extract_cta_with_quotes(self, router):
        """Test extracting CTA with quotes."""
        params = router._extract_params_from_text('post about sale with cta "Shop Now"', 'post')
        assert params.get('cta') == 'Shop Now'
    
    def test_extract_cta_without_quotes(self, router):
        """Test extracting CTA without quotes."""
        params = router._extract_params_from_text('post about event with cta Register Today', 'post')
        assert params.get('cta') == 'Register Today'
    
    def test_extract_cta_case_insensitive(self, router):
        """Test CTA extraction is case insensitive."""
        params = router._extract_params_from_text('post with CTA Learn More', 'post')
        assert params.get('cta') == 'Learn More'
    
    def test_cta_removed_from_topic(self, router):
        """Test that CTA is removed from topic extraction."""
        params = router._extract_params_from_text('post about our new product with cta Shop Now', 'post')
        assert params.get('cta') == 'Shop Now'
        # Topic should not include the CTA part
        topic = params.get('topic', '')
        assert 'with cta' not in topic.lower()
    
    # Test combined extraction
    def test_extract_platform_and_mood_together(self, router):
        """Test extracting both platform and mood from same input."""
        params = router._extract_params_from_text('excited Instagram post about weekend sale', 'post')
        assert params.get('platform') == 'instagram'
        assert params.get('mood') == 'excited'
        assert 'weekend sale' in params.get('topic', '')
    
    def test_extract_all_params_together(self, router):
        """Test extracting platform, mood, and CTA together."""
        params = router._extract_params_from_text(
            'urgent Facebook post about flash sale with cta Shop Now',
            'post'
        )
        assert params.get('platform') == 'facebook'
        assert params.get('mood') == 'urgent'
        assert params.get('cta') == 'Shop Now'
        assert 'flash sale' in params.get('topic', '')
    
    # Test natural language detection
    def test_classify_write_me_a_post(self, router):
        """Test detecting 'Write me a post about...' pattern."""
        result = router._classify_with_keywords('Write me a post about our new menu')
        assert result is not None
        assert result['task_type'] == 'post'
    
    def test_classify_i_need_an_email(self, router):
        """Test detecting 'I need an email for...' pattern."""
        result = router._classify_with_keywords('I need an email for newsletter')
        assert result is not None
        assert result['task_type'] == 'email'
    
    def test_classify_create_a_caption(self, router):
        """Test detecting 'Create a caption for...' pattern."""
        result = router._classify_with_keywords('Create a caption for my photo')
        assert result is not None
        assert result['task_type'] == 'caption'
    
    def test_classify_draft_a_script(self, router):
        """Test detecting 'Draft a script about...' pattern."""
        result = router._classify_with_keywords('Draft a script about our product')
        assert result is not None
        assert result['task_type'] == 'script'
    
    def test_classify_make_an_ad(self, router):
        """Test detecting 'Make an ad...' pattern."""
        result = router._classify_with_keywords('Make an ad for our sale')
        assert result is not None
        assert result['task_type'] == 'ad'
    
    def test_classify_natural_with_platform_and_mood(self, router):
        """Test natural language detection with platform and mood."""
        result = router._classify_with_keywords('Write me an excited Instagram post about our event')
        assert result is not None
        assert result['task_type'] == 'post'
        assert result['extracted_params'].get('platform') == 'instagram'
        assert result['extracted_params'].get('mood') == 'excited'
    
    # Test /quick command
    def test_parse_quick_command(self, router):
        """Test parsing /quick command."""
        result = router._parse_slash_command('/quick')
        assert result is not None
        assert result['task_type'] == 'quick_templates'
    
    def test_quick_in_command_map(self, router):
        """Test /quick is in COMMAND_MAP."""
        assert '/quick' in router.COMMAND_MAP
        assert router.COMMAND_MAP['/quick'] == 'quick_templates'
    
    # Test /session command
    def test_parse_session_command(self, router):
        """Test parsing /session command."""
        result = router._parse_slash_command('/session')
        assert result is not None
        assert result['task_type'] == 'batch_session'
    
    def test_session_in_command_map(self, router):
        """Test /session is in COMMAND_MAP."""
        assert '/session' in router.COMMAND_MAP
        assert router.COMMAND_MAP['/session'] == 'batch_session'
    
    # Test TASK_FIELDS includes new commands
    def test_task_fields_includes_quick_templates(self, router):
        """Test TASK_FIELDS includes quick_templates."""
        assert 'quick_templates' in router.TASK_FIELDS
    
    def test_task_fields_includes_batch_session(self, router):
        """Test TASK_FIELDS includes batch_session."""
        assert 'batch_session' in router.TASK_FIELDS
    
    # Test mood keywords are defined
    def test_mood_keywords_defined(self):
        """Test that MOOD_KEYWORDS constant is properly defined."""
        assert len(MOOD_KEYWORDS) >= 7  # At least 7 mood types
        assert 'excited' in MOOD_KEYWORDS
        assert 'professional' in MOOD_KEYWORDS
        assert 'casual' in MOOD_KEYWORDS
        assert 'urgent' in MOOD_KEYWORDS
        assert 'celebratory' in MOOD_KEYWORDS
        assert 'informative' in MOOD_KEYWORDS
        assert 'funny' in MOOD_KEYWORDS
    
    def test_mood_keywords_have_aliases(self):
        """Test that each mood has multiple keyword aliases."""
        for mood, keywords in MOOD_KEYWORDS.items():
            assert isinstance(keywords, list)
            assert len(keywords) > 0, f"Mood '{mood}' should have at least one keyword"
