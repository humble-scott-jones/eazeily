"""Tests for onboarding_service.py logging behavior"""
import logging
from unittest.mock import Mock, patch
from services.onboarding_service import OnboardingService


def test_process_url_logs_scraped_text_info(caplog):
    """Test that process_url logs scraped text information."""
    service = OnboardingService()
    mock_profile = Mock()
    mock_profile.get_writing_samples = Mock(return_value=[])
    mock_profile.set_writing_samples = Mock()
    
    with patch('services.scraper_service.scrape_url') as mock_scrape, \
         patch('services.scraper_service.extract_business_info') as mock_extract:
        
        mock_scrape.return_value = "This is some scraped text content from the website"
        mock_extract.return_value = {
            'business_name': 'Test Corp',
            'industry': 'Software',
            'key_customers': 'Small businesses',
            'key_offer': 'Free trial',
            'voice_tone_and_style': 'Professional',
            'sample_posts': ['Post 1']
        }
        
        with caplog.at_level(logging.INFO):
            result = service.process_url('https://example.com', mock_profile)
        
        assert result['success'] is True
        
        # Verify logging occurred
        log_messages = [record.message for record in caplog.records]
        
        # Check that scraped text info was logged
        assert any("Scraped" in msg and "chars from" in msg for msg in log_messages)
        
        # Check that extract_business_info return values were logged
        assert any("extract_business_info returned:" in msg and "business_name=Test Corp" in msg for msg in log_messages)
        
        # Check that final extracted_fields were logged
        assert any("Final extracted_fields:" in msg for msg in log_messages)


def test_process_url_logs_warning_when_no_text_scraped(caplog):
    """Test that process_url logs warning when scraping returns no text."""
    service = OnboardingService()
    mock_profile = Mock()
    
    with patch('services.scraper_service.scrape_url') as mock_scrape:
        mock_scrape.return_value = None
        
        with caplog.at_level(logging.WARNING):
            result = service.process_url('https://example.com', mock_profile)
        
        assert result['success'] is False
        
        # Verify warning was logged
        log_messages = [record.message for record in caplog.records]
        assert any("No text scraped from" in msg for msg in log_messages)


def test_process_url_logs_warning_when_no_fields_extracted(caplog):
    """Test that process_url logs warning when no fields are extracted."""
    service = OnboardingService()
    mock_profile = Mock()
    mock_profile.get_writing_samples = Mock(return_value=[])
    
    with patch('services.scraper_service.scrape_url') as mock_scrape, \
         patch('services.scraper_service.extract_business_info') as mock_extract:
        
        mock_scrape.return_value = "Some scraped text"
        # Return all None values - nothing extracted
        mock_extract.return_value = {
            'business_name': None,
            'industry': None,
            'key_customers': None,
            'key_offer': None,
            'voice_tone_and_style': None,
            'sample_posts': None
        }
        
        with caplog.at_level(logging.WARNING):
            result = service.process_url('https://example.com', mock_profile)
        
        assert result['success'] is True  # Still success, just no auto-fill
        assert result['extracted_fields'] == {}
        
        # Verify warnings were logged
        log_messages = [record.message for record in caplog.records]
        assert any("No fields were extracted from business_info!" in msg for msg in log_messages)
        assert any("No fields extracted from URL" in msg for msg in log_messages)
        
        # Verify the message is helpful
        assert "couldn't automatically extract" in result['message']
        assert "ask you some specific questions" in result['message']


def test_process_url_logs_all_return_values(caplog):
    """Test that process_url logs all values returned from extract_business_info."""
    service = OnboardingService()
    mock_profile = Mock()
    mock_profile.get_writing_samples = Mock(return_value=[])
    mock_profile.set_writing_samples = Mock()
    
    with patch('services.scraper_service.scrape_url') as mock_scrape, \
         patch('services.scraper_service.extract_business_info') as mock_extract:
        
        mock_scrape.return_value = "Scraped content"
        mock_extract.return_value = {
            'business_name': 'Test Business',
            'industry': 'Real Estate',
            'key_customers': 'Home buyers',
            'key_offer': 'Free consultation',
            'voice_tone_and_style': 'Warm and friendly',
            'sample_posts': ['Sample 1', 'Sample 2']
        }
        
        with caplog.at_level(logging.INFO):
            result = service.process_url('https://example.com', mock_profile)
        
        assert result['success'] is True
        
        # Verify all return values were logged
        log_messages = [record.message for record in caplog.records]
        
        combined_log = ' '.join(log_messages)
        assert "business_name=Test Business" in combined_log
        assert "industry=Real Estate" in combined_log
        assert "key_customers=Home buyers" in combined_log
        assert "key_offer=Free consultation" in combined_log
        assert "voice_tone_and_style=Warm and friendly" in combined_log
