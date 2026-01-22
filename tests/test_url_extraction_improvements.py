"""
Test improvements to URL extraction and user messaging.
"""
import pytest
from unittest.mock import Mock, patch
from services.scraper_service import extract_business_info, _extract_domain_name


def test_domain_name_fallback_for_business_name():
    """Test that domain name is used as fallback when business_name is not extracted."""
    
    # Mock AI response with no business_name
    mock_model = Mock()
    mock_model.generate_content.return_value.text = '''{
        "business_name": null,
        "industry": "Software / Tech / Startup",
        "key_customers": "Developers and engineers",
        "key_offer": "Fast and reliable cloud hosting",
        "brand_keywords": ["reliable", "fast", "cloud"],
        "niche_keywords": ["hosting", "infrastructure"],
        "voice_tone_and_style": "Professional and technical",
        "content_goals": ["Drive sign-ups"],
        "sample_posts": ["Great hosting starts here!"]
    }'''
    
    with patch('services.ai_service.get_generative_model', return_value=mock_model):
        result = extract_business_info("Sample content", "https://www.example-hosting.com")
        
        # Should use domain name as fallback
        assert result['business_name'] == 'Example Hosting'
        assert result['industry'] == 'Software / Tech / Startup'


def test_industry_always_provided():
    """Test that industry is always provided with Other/Custom fallback."""
    
    # Mock AI response with no industry
    mock_model = Mock()
    mock_model.generate_content.return_value.text = '''{
        "business_name": "Test Corp",
        "industry": null,
        "key_customers": "Everyone",
        "key_offer": "Quality products",
        "brand_keywords": [],
        "niche_keywords": [],
        "voice_tone_and_style": "Friendly",
        "content_goals": [],
        "sample_posts": []
    }'''
    
    with patch('services.ai_service.get_generative_model', return_value=mock_model):
        result = extract_business_info("Sample content", "https://www.testcorp.com")
        
        # Should provide default industry
        assert result['industry'] == 'Other / Custom'
        assert result['business_name'] == 'Test Corp'


def test_extract_domain_name():
    """Test domain name extraction helper."""
    assert _extract_domain_name("https://www.my-company.com") == "My Company"
    assert _extract_domain_name("https://example.org") == "Example"
    assert _extract_domain_name("http://test-site.net") == "Test Site"


def test_partial_extraction_includes_all_fields():
    """Test that result includes all expected fields even if some are empty."""
    
    mock_model = Mock()
    mock_model.generate_content.return_value.text = '''{
        "business_name": "Acme Inc",
        "industry": "Retail / Boutique",
        "key_customers": null,
        "key_offer": null,
        "brand_keywords": ["quality"],
        "niche_keywords": [],
        "voice_tone_and_style": null,
        "content_goals": ["Drive sales"],
        "sample_posts": ["Check out our new products!"]
    }'''
    
    with patch('services.ai_service.get_generative_model', return_value=mock_model):
        result = extract_business_info("Sample content", "https://www.acme.com")
        
        # All fields should be present
        assert 'business_name' in result
        assert 'industry' in result
        assert 'key_customers' in result
        assert 'key_offer' in result
        assert 'brand_keywords' in result
        assert 'niche_keywords' in result
        assert 'voice_tone_and_style' in result
        assert 'content_goals_ai' in result
        assert 'sample_posts' in result
        
        # Check extracted values
        assert result['business_name'] == 'Acme Inc'
        assert result['industry'] == 'Retail / Boutique'
        assert result['key_customers'] is None  # Should preserve None
        assert result['brand_keywords'] == ['quality']
        assert result['sample_posts'] == ['Check out our new products!']


def test_ai_prompt_contains_flexibility_guidance():
    """Test that the new prompt includes guidance about flexible extraction."""
    
    mock_model = Mock()
    mock_model.generate_content.return_value.text = '''{
        "business_name": "Test",
        "industry": "Other / Custom",
        "key_customers": "Customers",
        "key_offer": "Products",
        "brand_keywords": [],
        "niche_keywords": [],
        "voice_tone_and_style": "Casual",
        "content_goals": [],
        "sample_posts": ["Post 1", "Post 2"]
    }'''
    
    with patch('services.ai_service.get_generative_model', return_value=mock_model):
        result = extract_business_info("Sample text", "https://test.com")
        
        # Verify the model was called
        assert mock_model.generate_content.called
        
        # Check that the prompt includes flexibility keywords
        call_args = mock_model.generate_content.call_args[0][0]
        assert 'FLEXIBLE' in call_args or 'flexible' in call_args
        assert 'fallback' in call_args
        assert 'partial data' in call_args or 'partial' in call_args


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
