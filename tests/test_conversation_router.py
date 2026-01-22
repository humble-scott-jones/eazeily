"""Unit tests for ConversationRouter service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.conversation_router import ConversationRouter


class MockProfile:
    """Mock VoiceProfile for testing."""
    def __init__(self):
        self.business_name = 'Test Business'
        self.industry = 'Technology'


class TestConversationRouter:
    """Test suite for ConversationRouter."""
    
    @pytest.fixture
    def router(self):
        """Create a ConversationRouter instance."""
        return ConversationRouter()
    
    @pytest.fixture
    def mock_profile(self):
        """Create a mock profile."""
        return MockProfile()
    
    def test_parse_slash_command_post(self, router):
        """Test parsing /post command."""
        result = router._parse_slash_command('/post about our new product launch')
        assert result is not None
        assert result['task_type'] == 'post'
        assert 'topic' in result['extracted_params']
        assert 'new product launch' in result['extracted_params']['topic']
    
    def test_parse_slash_command_caption(self, router):
        """Test parsing /caption command."""
        result = router._parse_slash_command('/caption beach sunset vibes')
        assert result is not None
        assert result['task_type'] == 'caption'
        assert 'topic' in result['extracted_params']
    
    def test_parse_slash_command_script(self, router):
        """Test parsing /script command."""
        result = router._parse_slash_command('/script tutorial video')
        assert result is not None
        assert result['task_type'] == 'script'
    
    def test_parse_slash_command_reel_alias(self, router):
        """Test parsing /reel command (alias for script)."""
        result = router._parse_slash_command('/reel dance tutorial')
        assert result is not None
        assert result['task_type'] == 'script'
    
    def test_parse_slash_command_invalid(self, router):
        """Test parsing invalid slash command."""
        result = router._parse_slash_command('/invalid command')
        assert result is None
    
    def test_parse_slash_command_no_slash(self, router):
        """Test parsing input without slash."""
        result = router._parse_slash_command('post about something')
        assert result is None
    
    def test_extract_params_platform_instagram(self, router):
        """Test extracting Instagram platform."""
        params = router._extract_params_from_text('create an instagram post', 'post')
        assert params.get('platform') == 'instagram'
    
    def test_extract_params_platform_facebook(self, router):
        """Test extracting Facebook platform."""
        params = router._extract_params_from_text('facebook post about sale', 'post')
        assert params.get('platform') == 'facebook'
    
    def test_extract_params_platform_linkedin(self, router):
        """Test extracting LinkedIn platform."""
        params = router._extract_params_from_text('linkedin article needed', 'post')
        assert params.get('platform') == 'linkedin'
    
    def test_extract_params_platform_twitter(self, router):
        """Test extracting Twitter platform."""
        params = router._extract_params_from_text('tweet about our event', 'post')
        assert params.get('platform') == 'twitter'
    
    def test_extract_params_video_length(self, router):
        """Test extracting video length for scripts."""
        params = router._extract_params_from_text('30s tutorial video', 'script')
        assert params.get('video_length') == '30s'
        
        params = router._extract_params_from_text('60 seconds explainer', 'script')
        assert params.get('video_length') == '60s'
        
        # Test that partial matches are avoided (e.g., '115s' should not match '15s')
        params = router._extract_params_from_text('115s video', 'script')
        assert params.get('video_length') is None
        
        # Test '15 seconds' with spacing
        params = router._extract_params_from_text('15 seconds quick tip', 'script')
        assert params.get('video_length') == '15s'
    
    def test_extract_params_topic(self, router):
        """Test extracting topic from text."""
        params = router._extract_params_from_text('about our new cupcake flavor', 'post')
        assert 'topic' in params
        assert 'cupcake flavor' in params['topic'].lower()
    
    def test_get_missing_fields_post_empty(self, router):
        """Test missing fields for post with no params."""
        missing = router.get_missing_fields('post', {})
        assert 'topic' in missing
        assert 'platform' in missing
    
    def test_get_missing_fields_post_partial(self, router):
        """Test missing fields for post with only topic."""
        missing = router.get_missing_fields('post', {'topic': 'new product'})
        assert 'platform' in missing
        assert 'topic' not in missing
    
    def test_get_missing_fields_post_complete(self, router):
        """Test missing fields for post with all required params."""
        missing = router.get_missing_fields('post', {
            'topic': 'new product',
            'platform': 'instagram'
        })
        assert len(missing) == 0
    
    def test_get_missing_fields_caption(self, router):
        """Test missing fields for caption (only topic required)."""
        missing = router.get_missing_fields('caption', {})
        assert 'topic' in missing
        
        missing = router.get_missing_fields('caption', {'topic': 'beach sunset'})
        assert len(missing) == 0
    
    def test_get_missing_fields_script(self, router):
        """Test missing fields for script (topic and video_length required)."""
        missing = router.get_missing_fields('script', {})
        assert 'topic' in missing
        assert 'video_length' in missing
        
        missing = router.get_missing_fields('script', {'topic': 'tutorial'})
        assert 'video_length' in missing
        assert 'topic' not in missing
    
    def test_get_next_prompt_post_topic(self, router):
        """Test getting next prompt for missing topic."""
        prompt = router.get_next_prompt('post', ['topic', 'platform'])
        assert 'about' in prompt.lower()
    
    def test_get_next_prompt_post_platform(self, router):
        """Test getting next prompt for missing platform."""
        prompt = router.get_next_prompt('post', ['platform'])
        assert 'platform' in prompt.lower()
    
    def test_get_next_prompt_script_video_length(self, router):
        """Test getting next prompt for missing video length."""
        prompt = router.get_next_prompt('script', ['video_length'])
        assert 'long' in prompt.lower()
    
    def test_is_ready_to_generate_not_ready(self, router):
        """Test is_ready_to_generate when fields are missing."""
        assert not router.is_ready_to_generate('post', {})
        assert not router.is_ready_to_generate('post', {'topic': 'test'})
    
    def test_is_ready_to_generate_ready(self, router):
        """Test is_ready_to_generate when all fields present."""
        assert router.is_ready_to_generate('post', {
            'topic': 'new product',
            'platform': 'instagram'
        })
        
        assert router.is_ready_to_generate('caption', {
            'topic': 'beach sunset'
        })
        
        assert router.is_ready_to_generate('script', {
            'topic': 'tutorial',
            'video_length': '30s'
        })
    
    def test_parse_intent_empty_input(self, router, mock_profile):
        """Test parse_intent with empty input."""
        result = router.parse_intent('', mock_profile)
        assert result['intent'] == 'unknown'
        assert result['follow_up_needed'] is True
        assert result['follow_up_question'] is not None
    
    def test_parse_intent_slash_command(self, router, mock_profile):
        """Test parse_intent with slash command."""
        result = router.parse_intent('/post about new product on instagram', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        assert 'topic' in result['extracted_params']
        assert result['extracted_params'].get('platform') == 'instagram'
    
    def test_parse_intent_slash_command_incomplete(self, router, mock_profile):
        """Test parse_intent with incomplete slash command now applies smart defaults."""
        result = router.parse_intent('/post about new product', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        # With smart defaults, platform is now auto-filled with 'instagram'
        assert result['follow_up_needed'] is False
        assert result['extracted_params']['platform'] == 'instagram'
        assert result['extracted_params']['topic'] == 'new product'
    
    @patch('services.conversation_router.ConversationRouter._check_gemini')
    def test_parse_intent_gemini_unavailable(self, mock_check, router, mock_profile):
        """Test parse_intent uses keyword fallback when Gemini unavailable."""
        mock_check.return_value = False
        router.gemini_available = False
        
        result = router.parse_intent('I need a post about our sale', mock_profile)
        # Should use keyword fallback to detect 'post'
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        assert 'topic' in result['extracted_params']
        assert result['extracted_params']['topic'] == 'our sale'
    
    @patch('services.generation.gemini_adapter.call_gemini')
    def test_classify_with_gemini_post(self, mock_call, router, mock_profile):
        """Test classifying a post request with Gemini."""
        router.gemini_available = True
        
        mock_call.return_value = {
            'task_type': 'post',
            'topic': 'new product launch',
            'platform': 'instagram',
            'other_params': {}
        }
        
        result = router._classify_with_gemini('I need an Instagram post about our new product', mock_profile)
        assert result is not None
        assert result['task_type'] == 'post'
        assert result['extracted_params']['topic'] == 'new product launch'
        assert result['extracted_params']['platform'] == 'instagram'
    
    @patch('services.generation.gemini_adapter.call_gemini')
    def test_classify_with_gemini_caption(self, mock_call, router, mock_profile):
        """Test classifying a caption request with Gemini."""
        router.gemini_available = True
        
        mock_call.return_value = {
            'task_type': 'caption',
            'topic': 'beach sunset photo',
            'platform': None,
            'other_params': {}
        }
        
        result = router._classify_with_gemini('write a caption for my beach sunset photo', mock_profile)
        assert result is not None
        assert result['task_type'] == 'caption'
        assert result['extracted_params']['topic'] == 'beach sunset photo'
    
    @patch('services.generation.gemini_adapter.call_gemini')
    def test_classify_with_gemini_script(self, mock_call, router, mock_profile):
        """Test classifying a script request with Gemini."""
        router.gemini_available = True
        
        mock_call.return_value = {
            'task_type': 'script',
            'topic': 'tutorial video',
            'platform': None,
            'video_length': '30s',
            'other_params': {}
        }
        
        result = router._classify_with_gemini('I need a 30 second tutorial video script', mock_profile)
        assert result is not None
        assert result['task_type'] == 'script'
        assert result['extracted_params']['video_length'] == '30s'
    
    @patch('services.generation.gemini_adapter.call_gemini')
    def test_classify_with_gemini_unknown(self, mock_call, router, mock_profile):
        """Test classifying unknown request with Gemini."""
        router.gemini_available = True
        
        mock_call.return_value = {
            'task_type': 'unknown',
            'topic': None,
            'platform': None,
            'other_params': {}
        }
        
        result = router._classify_with_gemini('what is the weather today', mock_profile)
        assert result is None
    
    @patch('services.generation.gemini_adapter.call_gemini')
    def test_classify_with_gemini_failure(self, mock_call, router, mock_profile):
        """Test handling Gemini API failure."""
        router.gemini_available = True
        mock_call.return_value = None
        
        result = router._classify_with_gemini('create a post', mock_profile)
        assert result is None
    
    @patch('services.generation.gemini_adapter.call_gemini')
    def test_parse_intent_with_gemini(self, mock_call, router, mock_profile):
        """Test full parse_intent flow with Gemini classification."""
        router.gemini_available = True
        
        mock_call.return_value = {
            'task_type': 'post',
            'topic': 'summer sale',
            'platform': 'facebook',
            'other_params': {}
        }
        
        result = router.parse_intent('create a facebook post about our summer sale', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        assert result['extracted_params']['topic'] == 'summer sale'
        assert result['extracted_params']['platform'] == 'facebook'
        assert result['follow_up_needed'] is False
        assert len(result['missing_fields']) == 0
    
    @patch('services.generation.gemini_adapter.call_gemini')
    def test_parse_intent_gemini_partial(self, mock_call, router, mock_profile):
        """Test parse_intent with Gemini returning partial data now applies smart defaults."""
        router.gemini_available = True
        
        mock_call.return_value = {
            'task_type': 'ad',
            'topic': 'new product',
            'platform': None,
            'other_params': {}
        }
        
        result = router.parse_intent('I need an ad for our new product', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'ad'
        # With smart defaults, platform is now auto-filled with 'instagram'
        assert result['follow_up_needed'] is False
        assert result['extracted_params']['platform'] == 'instagram'
        assert result['follow_up_question'] is None  # No follow-up needed with defaults
    
    def test_all_task_types_have_configs(self, router):
        """Test that all task types in COMMAND_MAP have field configs.
        
        Exception: Commands that don't need field collection (list_profiles, switch_profile)
        can skip having a TASK_FIELDS entry since they execute immediately.
        """
        # Commands that don't need field collection
        IMMEDIATE_ACTIONS = {'list_profiles', 'switch_profile'}
        
        for task_type in router.COMMAND_MAP.values():
            if task_type not in IMMEDIATE_ACTIONS:
                assert task_type in router.TASK_FIELDS, f"Missing config for {task_type}"
    
    def test_all_required_fields_have_prompts(self, router):
        """Test that all required fields have prompt strings."""
        for task_type, config in router.TASK_FIELDS.items():
            required_fields = config.get('required', [])
            prompts = config.get('prompts', {})
            for field in required_fields:
                assert field in prompts, f"Missing prompt for {task_type}.{field}"
    
    def test_check_gemini_available(self, router):
        """Test _check_gemini method."""
        # This will depend on environment; just ensure it doesn't crash
        result = router._check_gemini()
        assert isinstance(result, bool)
    
    def test_multiple_platforms_extraction(self, router):
        """Test that only first platform is extracted when multiple mentioned."""
        params = router._extract_params_from_text('instagram and facebook post', 'post')
        # Should extract first mentioned
        assert params.get('platform') in ['instagram', 'facebook']
    
    def test_case_insensitive_platform_extraction(self, router):
        """Test platform extraction is case insensitive."""
        params = router._extract_params_from_text('INSTAGRAM post', 'post')
        assert params.get('platform') == 'instagram'
        
        params = router._extract_params_from_text('FaceBook post', 'post')
        assert params.get('platform') == 'facebook'
    
    def test_platform_extraction_word_boundaries(self, router):
        """Test platform extraction uses word boundaries to avoid partial matches."""
        # Should NOT match 'instagram' in 'instagramming'
        params = router._extract_params_from_text('instagramming is fun', 'post')
        assert params.get('platform') is None
        
        # Should match 'instagram' as a word
        params = router._extract_params_from_text('instagram post', 'post')
        assert params.get('platform') == 'instagram'
        
        # Should match with punctuation
        params = router._extract_params_from_text('post on instagram!', 'post')
        assert params.get('platform') == 'instagram'
    
    def test_topic_extraction_removes_filler_words(self, router):
        """Test that topic extraction removes common filler words."""
        params = router._extract_params_from_text('about our new product for customers', 'post')
        topic = params.get('topic', '')
        # Should have content but not the filler words
        assert 'new product' in topic.lower() or 'our new product customers' in topic.lower()
    
    # ===== NEW TESTS FOR ENHANCED PARAMETER EXTRACTION =====
    
    def test_extract_mood_excited(self, router):
        """Test extracting 'excited' mood from text."""
        params = router._extract_params_from_text('excited Instagram post about our sale', 'post')
        assert params.get('mood') == 'excited'
        assert params.get('platform') == 'instagram'
        assert 'sale' in params.get('topic', '').lower()
    
    def test_extract_mood_professional(self, router):
        """Test extracting 'professional' mood from text."""
        params = router._extract_params_from_text('professional LinkedIn post about leadership', 'post')
        assert params.get('mood') == 'professional'
        assert params.get('platform') == 'linkedin'
    
    def test_extract_mood_casual(self, router):
        """Test extracting 'casual' mood from text."""
        params = router._extract_params_from_text('casual Facebook post', 'post')
        assert params.get('mood') == 'casual'
        assert params.get('platform') == 'facebook'
    
    def test_extract_mood_urgent(self, router):
        """Test extracting 'urgent' mood from text."""
        params = router._extract_params_from_text('urgent post about limited time offer', 'post')
        assert params.get('mood') == 'urgent'
    
    def test_extract_mood_celebratory(self, router):
        """Test extracting 'celebratory' mood from text."""
        params = router._extract_params_from_text('celebratory post about our anniversary', 'post')
        assert params.get('mood') == 'celebratory'
    
    def test_extract_mood_informative(self, router):
        """Test extracting 'informative' mood from text."""
        params = router._extract_params_from_text('informative post with tips', 'post')
        assert params.get('mood') == 'informative'
    
    def test_extract_mood_funny(self, router):
        """Test extracting 'funny' mood from text."""
        params = router._extract_params_from_text('funny post about office life', 'post')
        assert params.get('mood') == 'funny'
    
    def test_extract_mood_inspiring(self, router):
        """Test extracting 'inspiring' mood from text."""
        params = router._extract_params_from_text('inspiring motivational post', 'post')
        assert params.get('mood') == 'inspiring'
    
    def test_extract_cta(self, router):
        """Test extracting CTA (call to action) from text."""
        params = router._extract_params_from_text('professional LinkedIn post about leadership with cta: Learn More', 'post')
        assert params.get('cta') == 'Learn More'
        assert params.get('mood') == 'professional'
        assert params.get('platform') == 'linkedin'
        # Topic should not contain the CTA pattern
        topic = params.get('topic', '')
        assert 'with cta' not in topic.lower()
    
    def test_extract_cta_with_space(self, router):
        """Test extracting CTA with space separator."""
        params = router._extract_params_from_text('post about sale with cta Shop Now', 'post')
        assert params.get('cta') == 'Shop Now'
    
    def test_smart_defaults_post_platform(self, router):
        """Test smart defaults apply instagram platform for posts."""
        params = router._apply_defaults_to_params('post', {'topic': 'sale'})
        assert params['platform'] == 'instagram'
    
    def test_smart_defaults_caption_platform(self, router):
        """Test smart defaults apply instagram platform for captions."""
        params = router._apply_defaults_to_params('caption', {'topic': 'beach'})
        assert params['platform'] == 'instagram'
    
    def test_smart_defaults_ad_platform(self, router):
        """Test smart defaults apply instagram platform for ads."""
        params = router._apply_defaults_to_params('ad', {'topic': 'product'})
        assert params['platform'] == 'instagram'
    
    def test_smart_defaults_script_video_length(self, router):
        """Test smart defaults apply 30s video length for scripts."""
        params = router._apply_defaults_to_params('script', {'topic': 'tutorial'})
        assert params['video_length'] == '30s'
    
    def test_smart_defaults_preserves_existing(self, router):
        """Test smart defaults don't override existing values."""
        params = router._apply_defaults_to_params('post', {'topic': 'sale', 'platform': 'facebook'})
        assert params['platform'] == 'facebook'  # Should keep facebook, not change to instagram
    
    def test_natural_language_post_detection(self, router):
        """Test natural language pattern 'create a post' is detected."""
        result = router._classify_with_keywords('create a post about our new cupcake flavor')
        assert result is not None
        assert result['task_type'] == 'post'
        assert 'cupcake flavor' in result['extracted_params'].get('topic', '').lower()
    
    def test_natural_language_email_detection(self, router):
        """Test natural language pattern 'I need an email' is detected."""
        result = router._classify_with_keywords('I need an email for newsletter')
        assert result is not None
        assert result['task_type'] == 'email'
    
    def test_natural_language_caption_detection(self, router):
        """Test natural language pattern 'write a caption' is detected."""
        result = router._classify_with_keywords('write a caption for beach photo')
        assert result is not None
        assert result['task_type'] == 'caption'
    
    def test_natural_language_script_detection(self, router):
        """Test natural language pattern 'create a script' is detected."""
        result = router._classify_with_keywords('create a script for tutorial video')
        assert result is not None
        assert result['task_type'] == 'script'
    
    def test_natural_language_ad_detection(self, router):
        """Test natural language pattern 'make an ad' is detected."""
        result = router._classify_with_keywords('make an ad for our new service')
        assert result is not None
        assert result['task_type'] == 'ad'
    
    def test_end_to_end_single_turn_excited_instagram(self, router, mock_profile):
        """Test end-to-end: 'excited Instagram post about our weekend sale' generates in one turn."""
        result = router.parse_intent('excited Instagram post about our weekend sale', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        assert result['follow_up_needed'] is False
        assert result['extracted_params']['mood'] == 'excited'
        assert result['extracted_params']['platform'] == 'instagram'
        assert 'weekend sale' in result['extracted_params']['topic'].lower()
    
    def test_end_to_end_single_turn_casual_facebook(self, router, mock_profile):
        """Test end-to-end: 'casual Facebook post about weekend plans' generates in one turn with smart defaults."""
        result = router.parse_intent('casual Facebook post about weekend plans', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        assert result['follow_up_needed'] is False
        assert result['extracted_params']['mood'] == 'casual'
        assert result['extracted_params']['platform'] == 'facebook'
        assert 'weekend plans' in result['extracted_params']['topic'].lower()
    
    def test_end_to_end_single_turn_slash_post_with_defaults(self, router, mock_profile):
        """Test end-to-end: '/post our new product' generates in one turn with smart defaults."""
        result = router.parse_intent('/post our new product', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        assert result['follow_up_needed'] is False
        assert result['extracted_params']['platform'] == 'instagram'  # Smart default
        assert 'new product' in result['extracted_params']['topic'].lower()
    
    def test_end_to_end_single_turn_30s_script(self, router, mock_profile):
        """Test end-to-end: '30s script about fitness tips' generates in one turn."""
        result = router.parse_intent('30s script about fitness tips', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'script'
        assert result['follow_up_needed'] is False
        assert result['extracted_params']['video_length'] == '30s'
        assert 'fitness tips' in result['extracted_params']['topic'].lower()
    
    def test_end_to_end_single_turn_script_with_defaults(self, router, mock_profile):
        """Test end-to-end: 'script about tutorial' generates in one turn with smart defaults."""
        result = router.parse_intent('script about tutorial', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'script'
        assert result['follow_up_needed'] is False
        assert result['extracted_params']['video_length'] == '30s'  # Smart default
    
    def test_end_to_end_single_turn_professional_linkedin_with_cta(self, router, mock_profile):
        """Test end-to-end: 'professional LinkedIn post about leadership with cta Learn More' generates in one turn."""
        result = router.parse_intent('professional LinkedIn post about leadership with cta: Learn More', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        assert result['follow_up_needed'] is False
        assert result['extracted_params']['mood'] == 'professional'
        assert result['extracted_params']['platform'] == 'linkedin'
        assert result['extracted_params']['cta'] == 'Learn More'
        assert 'leadership' in result['extracted_params']['topic'].lower()
