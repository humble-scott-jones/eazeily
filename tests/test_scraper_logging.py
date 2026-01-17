"""Tests for scraper_service.py logging behavior"""
import json
import logging
from services.scraper_service import extract_business_info


def test_extract_business_info_logs_input_and_output(monkeypatch, caplog):
    """Test that extract_business_info logs input text and Gemini response."""
    
    # Mock the AI model
    class FakeModel:
        def generate_content(self, prompt):
            class FakeResponse:
                text = json.dumps({
                    "business_name": "Tech Startup Inc",
                    "industry": "Software / Tech / Startup",
                    "key_customers": "Small to medium businesses looking for automation solutions.",
                    "key_offer": "Free 30-day trial with no credit card required",
                    "brand_keywords": ["innovative", "efficient"],
                    "niche_keywords": ["automation", "workflow"],
                    "voice_tone_and_style": "Professional and approachable",
                    "content_goals": ["Drive conversions"],
                    "sample_posts": ["Sample post 1"]
                })
            return FakeResponse()
    
    def fake_get_model():
        return FakeModel()
    
    monkeypatch.setattr('services.ai_service.get_generative_model', fake_get_model)
    
    scraped_text = "Tech Startup Inc provides cutting-edge automation tools for businesses. Our platform helps SMBs streamline their operations."
    
    with caplog.at_level(logging.INFO):
        result = extract_business_info(scraped_text)
    
    # Verify result is correct
    assert result["business_name"] == "Tech Startup Inc"
    assert result["industry"] == "Software / Tech / Startup"
    
    # Verify logging occurred
    log_messages = [record.message for record in caplog.records]
    
    # Check that input logging happened
    assert any("Extracting business info from" in msg and "chars of scraped text" in msg for msg in log_messages)
    
    # Check that Gemini response logging happened
    assert any("Gemini response length:" in msg and "chars" in msg for msg in log_messages)
    
    # Check that parsed fields were logged
    assert any("Parsed business_name: Tech Startup Inc" in msg for msg in log_messages)
    assert any("Parsed industry: Software / Tech / Startup" in msg for msg in log_messages)
    assert any("Parsed key_customers:" in msg for msg in log_messages)
    assert any("Parsed key_offer:" in msg for msg in log_messages)


def test_extract_business_info_logs_json_parse_error(monkeypatch, caplog):
    """Test that extract_business_info logs JSON parse errors with raw response."""
    
    # Mock the AI model to return invalid JSON
    class FakeModel:
        def generate_content(self, prompt):
            class FakeResponse:
                text = "This is not valid JSON at all"
            return FakeResponse()
    
    def fake_get_model():
        return FakeModel()
    
    monkeypatch.setattr('services.ai_service.get_generative_model', fake_get_model)
    
    scraped_text = "Some business content"
    
    with caplog.at_level(logging.ERROR):
        result = extract_business_info(scraped_text)
    
    # Should return fallback values
    assert "required_sections" in result
    
    # Verify error logging occurred
    log_messages = [record.message for record in caplog.records]
    
    # Check that JSON parse error was logged
    assert any("Failed to parse AI response as JSON:" in msg for msg in log_messages)
    
    # Check that raw response was logged
    assert any("Raw response that failed to parse:" in msg for msg in log_messages)


def test_extract_business_info_logs_general_exception(monkeypatch, caplog):
    """Test that extract_business_info logs general exceptions with traceback."""
    
    # Mock the AI model to raise an exception
    def fake_get_model():
        raise RuntimeError("AI service unavailable")
    
    monkeypatch.setattr('services.ai_service.get_generative_model', fake_get_model)
    
    scraped_text = "Some business content"
    
    with caplog.at_level(logging.ERROR):
        result = extract_business_info(scraped_text)
    
    # Should return fallback values
    assert "required_sections" in result
    
    # Verify error logging occurred
    log_messages = [record.message for record in caplog.records]
    
    # Check that exception was logged
    assert any("Failed to extract business info:" in msg for msg in log_messages)
