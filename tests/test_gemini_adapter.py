"""Tests for Gemini adapter and content generation."""
import json
import pytest
from unittest.mock import Mock, patch
from services.generation.gemini_adapter import (
    call_gemini,
    generate_content_with_profile,
    validate_generated_content,
    _build_prompt
)


class TestGeminiAdapter:
    """Test suite for Gemini adapter functionality."""
    
    def test_validate_generated_content_proposal(self):
        """Test validation of proposal content."""
        valid_proposal = {
            'titles': ['Title 1', 'Title 2', 'Title 3'],
            'summary': 'Executive summary',
            'benefits': ['Benefit 1', 'Benefit 2'],
            'cta': 'Contact us today'
        }
        assert validate_generated_content(valid_proposal, 'proposal') is True
        
        invalid_proposal = {
            'titles': ['Title 1'],
            'summary': 'Summary'
            # Missing benefits and cta
        }
        assert validate_generated_content(invalid_proposal, 'proposal') is False
    
    def test_validate_generated_content_review_reply(self):
        """Test validation of review reply content."""
        valid_reply = {
            'reply': 'Thank you for your feedback!',
            'short_reply': 'Thanks!'
        }
        assert validate_generated_content(valid_reply, 'review_reply') is True
        
        invalid_reply = {}
        assert validate_generated_content(invalid_reply, 'review_reply') is False
    
    def test_validate_generated_content_blog_post(self):
        """Test validation of blog post content."""
        valid_blog = {
            'titles': ['Title 1', 'Title 2', 'Title 3'],
            'content': 'Blog post content here...',
            'outline': ['Section 1', 'Section 2']
        }
        assert validate_generated_content(valid_blog, 'blog_post') is True
        
        invalid_blog = {
            'titles': ['Title 1']
            # Missing content
        }
        assert validate_generated_content(invalid_blog, 'blog_post') is False
    
    def test_validate_generated_content_social_post(self):
        """Test validation of social media post content."""
        valid_post = {'content': 'Post content'}
        assert validate_generated_content(valid_post, 'post') is True
        
        valid_caption = {'caption': 'Caption text'}
        assert validate_generated_content(valid_caption, 'post') is True
        
        valid_text = {'text': 'Text content'}
        assert validate_generated_content(valid_text, 'post') is True
        
        invalid_post = {'other_field': 'value'}
        assert validate_generated_content(invalid_post, 'post') is False
    
    def test_build_prompt_proposal(self):
        """Test proposal prompt building."""
        context = {
            'company': 'Test Co',
            'industry': 'Tech',
            'target_audience': 'Developers',
            'brand_voice': 'Professional',
            'brand_keywords': ['innovative', 'reliable'],
            'niche_keywords': ['API', 'cloud'],
            'customers': ['Enterprise', 'Startups'],
            'scraped_meta': {}
        }
        
        prompt = _build_prompt('proposal', 'Partnership proposal', None, context)
        
        assert 'Company: Test Co' in prompt
        assert 'Industry: Tech' in prompt
        assert 'Proposal' in prompt
        assert 'Partnership proposal' in prompt
        assert 'three compelling title options' in prompt.lower()
    
    def test_build_prompt_review_reply(self):
        """Test review reply prompt building."""
        context = {
            'company': 'Test Co',
            'industry': 'Retail',
            'brand_voice': 'Friendly',
            'brand_keywords': [],
            'niche_keywords': [],
            'customers': [],
            'scraped_meta': {}
        }
        
        prompt = _build_prompt('review_reply', 'Great service!', None, context)
        
        assert 'Company: Test Co' in prompt
        assert 'Review Reply' in prompt
        assert 'Great service!' in prompt
        assert 'acknowledgment' in prompt.lower()
    
    def test_build_prompt_blog_post(self):
        """Test blog post prompt building."""
        context = {
            'company': 'Test Co',
            'industry': 'Marketing',
            'target_audience': 'Small businesses',
            'brand_voice': 'Educational',
            'brand_keywords': ['growth', 'strategy'],
            'niche_keywords': ['SEO', 'content'],
            'customers': [],
            'scraped_meta': {}
        }
        
        prompt = _build_prompt('blog_post', 'How to grow your business', None, context)
        
        assert 'Company: Test Co' in prompt
        assert 'Blog Post' in prompt
        assert 'How to grow your business' in prompt
        assert 'three title options' in prompt.lower()
        assert 'meta description' in prompt.lower()
    
    def test_build_prompt_social_post(self):
        """Test social media post prompt building."""
        context = {
            'company': 'Test Co',
            'industry': 'Tech',
            'brand_voice': 'Casual',
            'brand_keywords': ['fun', 'innovative'],
            'niche_keywords': [],
            'customers': ['Millennials'],
            'target_audience': 'Young professionals',
            'scraped_meta': {}
        }
        
        prompt = _build_prompt('post', 'New product launch', 'instagram', context)
        
        assert 'Company: Test Co' in prompt
        assert 'instagram' in prompt.lower()
        assert 'New product launch' in prompt
        assert 'Target Audience: Young professionals' in prompt
        assert 'Key Audiences: Millennials' in prompt
    
    @patch('services.generation.gemini_adapter.genai')
    def test_call_gemini_success(self, mock_genai):
        """Test successful Gemini API call."""
        # Mock the client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '{"content": "Generated content"}'
        
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        with patch.dict('os.environ', {'GENAI_API_KEY': 'test-key'}):
            result = call_gemini("Test prompt", context={'key': 'value'})
        
        assert result is not None
        assert result['content'] == 'Generated content'
    
    @patch('services.generation.gemini_adapter.genai')
    def test_call_gemini_json_parsing(self, mock_genai):
        """Test JSON parsing with markdown code blocks."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.text = '```json\n{"content": "Generated"}\n```'
        
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client
        
        with patch.dict('os.environ', {'GENAI_API_KEY': 'test-key'}):
            result = call_gemini("Test prompt")
        
        assert result is not None
        assert result['content'] == 'Generated'
    
    @patch('services.generation.gemini_adapter.genai', None)
    def test_call_gemini_no_client(self):
        """Test Gemini call when client is unavailable."""
        result = call_gemini("Test prompt")
        assert result is None
    
    def test_generate_content_with_profile_structure(self):
        """Test that generate_content_with_profile structures context correctly."""
        profile = {
            'company': 'Test Co',
            'business_name': 'Test Company',
            'industry': 'Tech',
            'target_audience': 'Developers',
            'customers': ['Enterprise', 'SMB'],
            'brand_voice': 'Professional',
            'tone': 'Friendly',
            'brand_keywords': ['innovative'],
            'niche_keywords': ['API'],
            'key_offer': 'Best API tools',
            'scraped_meta': {
                'key_customers': 'Tech companies',
                'business_name': 'Official Name'
            }
        }
        
        with patch('services.generation.gemini_adapter.call_gemini') as mock_call:
            mock_call.return_value = {'content': 'Generated'}
            
            result = generate_content_with_profile(
                profile,
                'post',
                'New feature announcement',
                'linkedin'
            )
            
            # Verify call_gemini was called
            assert mock_call.called
            # Get the prompt that was passed
            call_args = mock_call.call_args
            prompt = call_args[0][0]
            
            # Verify key profile data is in the prompt
            assert 'Test Co' in prompt
            assert 'Tech' in prompt
            assert 'Developers' in prompt
            assert 'Professional' in prompt or 'Friendly' in prompt
            assert 'innovative' in prompt
