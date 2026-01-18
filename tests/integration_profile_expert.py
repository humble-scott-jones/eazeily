#!/usr/bin/env python3
"""
Integration test script for the profile expert feature.
This demonstrates the AI-powered profile suggestions in action.
"""

import os
import sys
from unittest.mock import Mock, patch

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.profile_expert import (
    build_context,
    parse_suggestions,
    generate_profile_suggestions_sync,
)


def test_build_context():
    """Test that context is built correctly from profile."""
    print("\n=== Testing Context Building ===")
    
    profile = {
        'company': 'Eazeily',
        'business_name': 'Eazeily',
        'industry': 'Software',
        'tone': 'Friendly and helpful',
        'target_audience': 'Small business owners',
        'key_offer': 'AI-powered social media content',
        'writing_samples': [
            'Just shipped a new feature! 🚀',
            'Your brand voice matters.'
        ]
    }
    
    context = build_context(profile, 'target_audience')
    
    print(f"Business Name: {context['business_name']}")
    print(f"Industry: {context['industry']}")
    print(f"Brand Voice: {context['brand_voice']}")
    print(f"Key Offer: {context['key_offer']}")
    print(f"Writing Samples:\n{context['writing_samples']}")
    
    assert context['business_name'] == 'Eazeily'
    assert context['industry'] == 'Software'
    assert 'Friendly' in context['brand_voice']
    
    print("✅ Context building works correctly!")


def test_parse_suggestions():
    """Test that AI responses are parsed correctly."""
    print("\n=== Testing Suggestion Parsing ===")
    
    ai_response = """1. Small business owners aged 30-50 who struggle with social media.
They understand the importance of being online.

2. Marketing managers at mid-sized companies who need to scale content.
They're looking for efficient solutions.

3. Solopreneurs who want to establish thought leadership.
They need help crafting professional content."""
    
    suggestions = parse_suggestions(ai_response)
    
    print(f"Parsed {len(suggestions)} suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"\n{i}. {suggestion[:80]}...")
    
    assert len(suggestions) == 3
    assert 'Small business owners' in suggestions[0]
    assert 'Marketing managers' in suggestions[1]
    assert 'Solopreneurs' in suggestions[2]
    
    print("\n✅ Suggestion parsing works correctly!")


def test_generate_with_mock():
    """Test suggestion generation with mocked OpenAI."""
    print("\n=== Testing AI Suggestion Generation (Mocked) ===")
    
    profile = {
        'company': 'Eazeily',
        'industry': 'Software',
        'brand_voice': 'Friendly and helpful',
        'target_audience': 'Small business owners',
        'key_offer': 'AI-powered social media content',
        'writing_samples': ['Test post 1', 'Test post 2']
    }
    
    # Mock the OpenAI response
    with patch('services.profile_expert.get_client') as mock_get_client:
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """1. Busy small business owners (1-10 employees) aged 30-50 who struggle with maintaining consistent social media. They know they need to be online but lack time and expertise.

2. Solopreneurs and freelancers who understand social media's importance but feel overwhelmed. They're looking for a way to stay visible without becoming full-time content creators.

3. Marketing managers at small agencies who need to scale content for multiple clients. They want reliable, brand-consistent output they can quickly review and post."""
        
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client
        
        result = generate_profile_suggestions_sync('target_audience', profile)
        
        print(f"\nResult Success: {result['success']}")
        print(f"Field: {result['field']}")
        print(f"Number of Suggestions: {len(result['suggestions'])}")
        print(f"\nSuggestions:")
        for i, suggestion in enumerate(result['suggestions'], 1):
            print(f"\n{i}. {suggestion[:100]}...")
        
        assert result['success'] is True
        assert result['field'] == 'target_audience'
        assert len(result['suggestions']) == 3
        assert 'context' in result
        
        print("\n✅ AI suggestion generation works correctly!")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 60)
    print("Profile Expert Integration Tests")
    print("=" * 60)
    
    try:
        test_build_context()
        test_parse_suggestions()
        test_generate_with_mock()
        
        print("\n" + "=" * 60)
        print("✅ All Integration Tests Passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(run_all_tests())
