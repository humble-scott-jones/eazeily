"""Tests for OnboardingService - conversational onboarding logic."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from services.onboarding_service import OnboardingService
from models import VoiceProfile


@pytest.fixture
def onboarding_service():
    """Create an OnboardingService instance."""
    return OnboardingService()


@pytest.fixture
def mock_profile():
    """Create a mock VoiceProfile."""
    profile = Mock()
    profile.business_name = None
    profile.industry = None
    profile.target_audience = None
    profile.brand_voice = None
    profile.key_offer = None
    profile.get_writing_samples = Mock(return_value=[])
    profile.set_writing_samples = Mock()
    return profile


def test_get_missing_fields_all_missing(onboarding_service, mock_profile):
    """Test get_missing_fields returns all fields when profile is empty."""
    missing = onboarding_service.get_missing_fields(mock_profile)
    
    assert len(missing) == 6
    assert 'business_name' in missing
    assert 'industry' in missing
    assert 'target_audience' in missing
    assert 'brand_voice' in missing
    assert 'key_offer' in missing
    assert 'writing_samples' in missing


def test_get_missing_fields_partial(onboarding_service, mock_profile):
    """Test get_missing_fields returns only missing fields."""
    mock_profile.business_name = "Test Business"
    mock_profile.industry = "Real Estate"
    
    missing = onboarding_service.get_missing_fields(mock_profile)
    
    assert len(missing) == 4
    assert 'business_name' not in missing
    assert 'industry' not in missing
    assert 'target_audience' in missing


def test_get_missing_fields_none_missing(onboarding_service, mock_profile):
    """Test get_missing_fields returns empty list when profile is complete."""
    mock_profile.business_name = "Test Business"
    mock_profile.industry = "Real Estate"
    mock_profile.target_audience = "Home buyers"
    mock_profile.brand_voice = "Professional"
    mock_profile.key_offer = "Free consultation"
    mock_profile.get_writing_samples = Mock(return_value=["Sample 1"])
    
    missing = onboarding_service.get_missing_fields(mock_profile)
    
    assert len(missing) == 0


def test_get_next_question(onboarding_service):
    """Test get_next_question returns appropriate prompt."""
    question = onboarding_service.get_next_question(['business_name'])
    assert "business name" in question.lower()
    
    question = onboarding_service.get_next_question(['target_audience'])
    assert "ideal customer" in question.lower()


def test_get_next_question_empty(onboarding_service):
    """Test get_next_question returns empty string when no fields missing."""
    question = onboarding_service.get_next_question([])
    assert question == ""


def test_update_profile_field_simple(onboarding_service, mock_profile):
    """Test update_profile_field updates simple fields."""
    onboarding_service.update_profile_field(mock_profile, 'business_name', 'Test Corp')
    
    assert mock_profile.business_name == 'Test Corp'


def test_update_profile_field_writing_samples_list(onboarding_service, mock_profile):
    """Test update_profile_field handles writing samples as list."""
    samples = ["Sample 1", "Sample 2"]
    onboarding_service.update_profile_field(mock_profile, 'writing_samples', samples)
    
    mock_profile.set_writing_samples.assert_called_once_with(samples)


def test_update_profile_field_writing_samples_string(onboarding_service, mock_profile):
    """Test update_profile_field handles writing samples as string."""
    samples_text = "Sample 1\n\nSample 2"
    onboarding_service.update_profile_field(mock_profile, 'writing_samples', samples_text)
    
    # Should split by double newlines
    mock_profile.set_writing_samples.assert_called_once()
    called_samples = mock_profile.set_writing_samples.call_args[0][0]
    assert len(called_samples) == 2
    assert "Sample 1" in called_samples
    assert "Sample 2" in called_samples


def test_is_profile_complete_incomplete(onboarding_service, mock_profile):
    """Test is_profile_complete returns False for incomplete profile."""
    is_complete, missing = onboarding_service.is_profile_complete(mock_profile)
    
    assert is_complete is False
    assert len(missing) > 0


def test_is_profile_complete_complete(onboarding_service, mock_profile):
    """Test is_profile_complete returns True for complete profile."""
    mock_profile.business_name = "Test Business"
    mock_profile.industry = "Real Estate"
    mock_profile.target_audience = "Home buyers"
    mock_profile.brand_voice = "Professional"
    mock_profile.key_offer = "Free consultation"
    mock_profile.get_writing_samples = Mock(return_value=["Sample 1"])
    
    is_complete, missing = onboarding_service.is_profile_complete(mock_profile)
    
    assert is_complete is True
    assert len(missing) == 0


def test_detect_url_with_http(onboarding_service):
    """Test detect_url finds HTTP URLs."""
    url = onboarding_service.detect_url("Check out https://example.com for more info")
    assert url == "https://example.com"


def test_detect_url_with_www(onboarding_service):
    """Test detect_url finds www URLs."""
    url = onboarding_service.detect_url("Visit www.example.com today")
    assert url == "www.example.com"


def test_detect_url_plain_domain(onboarding_service):
    """Test detect_url finds plain domain names."""
    url = onboarding_service.detect_url("My website is example.com")
    assert url == "example.com"


def test_detect_url_none(onboarding_service):
    """Test detect_url returns None when no URL present."""
    url = onboarding_service.detect_url("Just some random text")
    assert url is None


def test_detect_url_strips_punctuation(onboarding_service):
    """Test detect_url strips trailing punctuation."""
    url = onboarding_service.detect_url("Visit https://example.com!")
    assert url == "https://example.com"


@patch('services.scraper_service.scrape_url')
@patch('services.scraper_service.extract_business_info')
def test_process_url_success(mock_extract, mock_scrape, onboarding_service, mock_profile):
    """Test process_url successfully scrapes and extracts data."""
    # Setup mocks
    mock_scrape.return_value = "Some scraped text"
    mock_extract.return_value = {
        'business_name': 'Test Corp',
        'industry': 'Software',
        'key_customers': 'Small businesses',
        'key_offer': 'Free trial',
        'voice_tone_and_style': 'Professional and friendly',
        'sample_posts': ['Post 1', 'Post 2']
    }
    
    result = onboarding_service.process_url('https://example.com', mock_profile)
    
    assert result['success'] is True
    assert 'Test Corp' in result['message']
    assert 'extracted_fields' in result
    assert result['extracted_fields']['business_name'] == 'Test Corp'


@patch('services.scraper_service.scrape_url')
def test_process_url_scrape_fails(mock_scrape, onboarding_service, mock_profile):
    """Test process_url handles scraping failure gracefully."""
    mock_scrape.return_value = None
    
    result = onboarding_service.process_url('https://example.com', mock_profile)
    
    assert result['success'] is False
    assert 'error' in result
    assert 'describe your brand' in result['message'].lower()


def test_process_url_invalid_url(onboarding_service, mock_profile):
    """Test process_url handles invalid URLs."""
    result = onboarding_service.process_url('not a url', mock_profile)
    
    assert result['success'] is False
    # URL normalization adds https://, but scraping fails due to invalid hostname
    # So we get the "couldn't access" message rather than "invalid URL"
    assert "couldn't" in result['message'].lower() or 'invalid' in result['message'].lower()


@patch('services.ai_service.get_generative_model')
def test_process_description_with_ai(mock_get_model, onboarding_service, mock_profile):
    """Test process_description uses AI to extract fields."""
    # Setup mock AI model
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"business_name": "Test Business", "industry": "Real Estate"}'
    mock_model.generate_content.return_value = mock_response
    mock_get_model.return_value = mock_model
    
    result = onboarding_service.process_description(
        "I run a real estate business called Test Business",
        mock_profile
    )
    
    assert result['success'] is True
    assert 'extracted_fields' in result
    assert result['extracted_fields'].get('business_name') == 'Test Business'


@patch('services.ai_service.get_generative_model')
def test_process_description_with_context(mock_get_model, onboarding_service, mock_profile):
    """Test process_description with specific field context."""
    mock_get_model.return_value = None  # AI not available
    
    result = onboarding_service.process_description(
        "We target busy parents",
        mock_profile,
        context='target_audience'
    )
    
    assert result['success'] is True
    assert result['field_name'] == 'target_audience'
    assert result['extracted_fields']['target_audience'] == 'We target busy parents'


@patch('services.ai_service.get_generative_model')
def test_process_description_no_ai(mock_get_model, onboarding_service, mock_profile):
    """Test process_description handles missing AI gracefully."""
    mock_get_model.return_value = None
    
    result = onboarding_service.process_description(
        "Some description",
        mock_profile
    )
    
    assert result['success'] is False
    assert 'specific information' in result['message'].lower()
