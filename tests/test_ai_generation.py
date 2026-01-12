"""
Tests for AI-powered content generation with Gemini.

Verifies that:
1. AI generation is attempted when API key is present
2. Fallback to template works when AI fails
3. Quality checks are applied to AI output
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from generator import _generate_caption_with_ai, build_caption_body


def test_ai_generation_called_when_enabled():
    """Test that AI generation is attempted when USE_GEMINI_FOR_POSTS is True."""
    with patch('generator.USE_GEMINI_FOR_POSTS', True):
        with patch('services.generation.gemini_adapter.call_gemini') as mock_gemini:
            # Mock successful AI response
            mock_gemini.return_value = {
                'text': """Just launched our eco-friendly packaging! 🌱

Here's what makes it special:
1. 100% biodegradable materials
2. Carbon-neutral production
3. Recyclable and compostable

Ready to make a difference? Check out our new line today!"""
            }
            
            result = _generate_caption_with_ai(
                industry='Retail',
                tone='friendly',
                pillar_name='Product/Offer',
                pillar_hint='Highlight our eco-friendly packaging',
                platform='instagram',
                brand_keywords=['sustainable', 'eco-friendly'],
                goals=['awareness', 'sales'],
                company='EcoShop'
            )
            
            # Should have called Gemini
            assert mock_gemini.called
            # Should return the AI-generated content
            assert result is not None
            assert 'eco-friendly packaging' in result.lower()
            assert 'platform tip:' not in result.lower()  # Should not be template


def test_ai_generation_rejects_banned_phrases():
    """Test that AI output with banned phrases is rejected."""
    with patch('services.generation.gemini_adapter.call_gemini') as mock_gemini:
        # Mock AI response with banned phrases
        mock_gemini.return_value = {
            'text': """Platform tip: You should post about eco-friendly products.
Make sure to add hashtags and engage with followers."""
        }
        
        result = _generate_caption_with_ai(
            industry='Retail',
            tone='friendly',
            pillar_name='Product/Offer',
            pillar_hint='Highlight products',
            platform='instagram',
            brand_keywords=['eco'],
            goals=['sales'],
            company='EcoShop'
        )
        
        # Should reject the output due to banned phrases
        assert result is None


def test_ai_generation_handles_api_failure():
    """Test that AI generation handles API failures gracefully."""
    with patch('services.generation.gemini_adapter.call_gemini') as mock_gemini:
        # Mock API failure
        mock_gemini.side_effect = Exception("API connection failed")
        
        result = _generate_caption_with_ai(
            industry='Retail',
            tone='friendly',
            pillar_name='Product/Offer',
            pillar_hint='Highlight products',
            platform='instagram',
            brand_keywords=['eco'],
            goals=['sales'],
            company='EcoShop'
        )
        
        # Should return None on failure
        assert result is None


def test_build_caption_body_tries_ai_first():
    """Test that build_caption_body tries AI generation before template."""
    with patch('generator.USE_GEMINI_FOR_POSTS', True):
        with patch('generator._generate_caption_with_ai') as mock_ai:
            # Mock successful AI generation
            mock_ai.return_value = "Great AI-generated content!"
            
            result = build_caption_body(
                industry='Retail',
                tone='friendly',
                pillar_name='Product/Offer',
                pillar_hint='Highlight products',
                platform='instagram',
                brand_keywords=['eco'],
                goals=['sales'],
                company='EcoShop'
            )
            
            # Should have tried AI first
            assert mock_ai.called
            # Should return AI result
            assert result == "Great AI-generated content!"


def test_build_caption_body_falls_back_to_template():
    """Test that build_caption_body falls back to template when AI fails."""
    with patch('generator.USE_GEMINI_FOR_POSTS', True):
        with patch('generator._generate_caption_with_ai') as mock_ai:
            # Mock AI failure
            mock_ai.return_value = None
            
            result = build_caption_body(
                industry='Retail',
                tone='friendly',
                pillar_name='Product/Offer',
                pillar_hint='Highlight products',
                platform='instagram',
                brand_keywords=['eco'],
                goals=['sales'],
                company='EcoShop'
            )
            
            # Should have tried AI first
            assert mock_ai.called
            # Should return template (contains "Platform tip:")
            assert 'Platform tip:' in result
            assert 'CTA:' in result


def test_ai_generation_cleans_markdown():
    """Test that AI generation cleans markdown formatting from response."""
    with patch('services.generation.gemini_adapter.call_gemini') as mock_gemini:
        # Mock response with markdown code blocks
        mock_gemini.return_value = {
            'text': '```\nGreat content here!\n\n1. First point\n2. Second point\n\nTry it now!\n```'
        }
        
        result = _generate_caption_with_ai(
            industry='Retail',
            tone='friendly',
            pillar_name='Product/Offer',
            pillar_hint='Highlight products',
            platform='instagram',
            brand_keywords=['eco'],
            goals=['sales'],
            company='EcoShop'
        )
        
        # Should clean markdown and return content
        assert result is not None
        assert '```' not in result
        assert 'Great content here!' in result


def test_ai_generation_includes_voice_profile_context():
    """Test that voice profile context is included in AI prompt."""
    with patch('services.generation.gemini_adapter.call_gemini') as mock_gemini:
        mock_gemini.return_value = {'text': 'Generated content'}
        
        voice_profile = {
            'include_phrases': ['game-changer', 'eco-warrior'],
            'example_lines': ['Transform your daily routine with our sustainable solutions.']
        }
        
        result = _generate_caption_with_ai(
            industry='Retail',
            tone='friendly',
            pillar_name='Product/Offer',
            pillar_hint='Highlight products',
            platform='instagram',
            brand_keywords=['eco'],
            goals=['sales'],
            company='EcoShop',
            voice_profile=voice_profile
        )
        
        # Should have called Gemini with prompt containing voice profile
        assert mock_gemini.called
        call_args = mock_gemini.call_args
        prompt = call_args[0][0]  # First positional argument
        
        # Check that voice profile elements are in prompt
        assert 'game-changer' in prompt or 'eco-warrior' in prompt
        assert 'Transform your daily routine' in prompt


def test_ai_generation_prompt_structure():
    """Test that AI generation creates proper prompt structure."""
    with patch('services.generation.gemini_adapter.call_gemini') as mock_gemini:
        mock_gemini.return_value = {'text': 'Content'}
        
        _generate_caption_with_ai(
            industry='Coffee Shop',
            tone='playful',
            pillar_name='Educational',
            pillar_hint='Share brewing tips',
            platform='instagram',
            brand_keywords=['artisan', 'organic'],
            goals=['engagement'],
            company='Brew Masters',
            theme='Morning rituals'
        )
        
        # Check the prompt structure
        call_args = mock_gemini.call_args
        prompt = call_args[0][0]
        
        # Verify key elements in prompt
        assert 'instagram' in prompt.lower()
        assert 'Coffee Shop' in prompt
        assert 'artisan' in prompt
        assert 'organic' in prompt
        assert 'Brew Masters' in prompt
        assert 'engagement' in prompt
        assert 'call-to-action' in prompt.lower() or 'CTA' in prompt
        assert 'NO guidance phrases' in prompt or 'NO meta commentary' in prompt
