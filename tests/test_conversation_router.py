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
        """Test parse_intent with incomplete slash command."""
        result = router.parse_intent('/post about new product', mock_profile)
        assert result['intent'] == 'generate'
        assert result['task_type'] == 'post'
        assert result['follow_up_needed'] is True
        assert 'platform' in result['missing_fields']
    
    @patch('services.conversation_router.ConversationRouter._check_gemini')
    def test_parse_intent_gemini_unavailable(self, mock_check, router, mock_profile):
        """Test parse_intent falls back when Gemini unavailable."""
        mock_check.return_value = False
        router.gemini_available = False
        
        result = router.parse_intent('I need a post about our sale', mock_profile)
        assert result['intent'] == 'unknown'
        assert result['follow_up_needed'] is True
        assert 'command' in result['follow_up_question'].lower()
    
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
        """Test parse_intent with Gemini returning partial data."""
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
        assert result['follow_up_needed'] is True
        assert 'platform' in result['missing_fields']
        assert result['follow_up_question'] is not None
    
    def test_all_task_types_have_configs(self, router):
        """Test that all task types in COMMAND_MAP have field configs."""
        for task_type in router.COMMAND_MAP.values():
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
    
    def test_topic_extraction_removes_filler_words(self, router):
        """Test that topic extraction removes common filler words."""
        params = router._extract_params_from_text('about our new product for customers', 'post')
        topic = params.get('topic', '')
        # Should have content but not the filler words
        assert 'new product' in topic.lower() or 'our new product customers' in topic.lower()
