"""Tests for scraper_service.py"""
import json


def test_extract_business_info_with_ai(monkeypatch):
    """Test extract_business_info function with mocked AI."""
    from services.scraper_service import extract_business_info
    
    # Mock the AI model
    class FakeModel:
        def generate_content(self, prompt):
            class FakeResponse:
                text = json.dumps({
                    "business_name": "Tech Startup Inc",
                    "industry": "Software / Tech / Startup",
                    "key_customers": "Small to medium businesses looking for automation solutions."
                })
            return FakeResponse()
    
    def fake_get_model():
        return FakeModel()
    
    monkeypatch.setattr('services.ai_service.get_generative_model', fake_get_model)
    
    scraped_text = "Tech Startup Inc provides cutting-edge automation tools for businesses. Our platform helps SMBs streamline their operations."
    
    result = extract_business_info(scraped_text)
    
    assert result["business_name"] == "Tech Startup Inc"
    assert result["industry"] == "Software / Tech / Startup"
    assert result["key_customers"] == "Small to medium businesses looking for automation solutions."


def test_extract_business_info_without_ai(monkeypatch):
    """Test extract_business_info when AI is unavailable."""
    from services.scraper_service import extract_business_info
    
    # Mock AI service to return None
    monkeypatch.setattr('services.ai_service.get_generative_model', lambda: None)
    
    scraped_text = "Some business content"
    result = extract_business_info(scraped_text)
    
    # Should return None values when AI is unavailable
    assert result["business_name"] is None
    assert result["industry"] is None
    assert result["key_customers"] is None


def test_extract_business_info_handles_json_error(monkeypatch):
    """Test extract_business_info handles invalid JSON from AI."""
    from services.scraper_service import extract_business_info
    
    # Mock the AI model to return invalid JSON
    class FakeModel:
        def generate_content(self, prompt):
            class FakeResponse:
                text = "This is not valid JSON"
            return FakeResponse()
    
    def fake_get_model():
        return FakeModel()
    
    monkeypatch.setattr('services.ai_service.get_generative_model', fake_get_model)
    
    scraped_text = "Some business content"
    result = extract_business_info(scraped_text)
    
    # Should return None values when JSON parsing fails
    assert result["business_name"] is None
    assert result["industry"] is None
    assert result["key_customers"] is None


def test_extract_business_info_strips_markdown(monkeypatch):
    """Test that extract_business_info strips markdown code blocks from AI response."""
    from services.scraper_service import extract_business_info
    
    # Mock the AI model to return JSON wrapped in markdown
    class FakeModel:
        def generate_content(self, prompt):
            class FakeResponse:
                text = '''```json
{
    "business_name": "Cafe Deluxe",
    "industry": "Restaurant / Café",
    "key_customers": "Coffee lovers and breakfast enthusiasts."
}
```'''
            return FakeResponse()
    
    def fake_get_model():
        return FakeModel()
    
    monkeypatch.setattr('services.ai_service.get_generative_model', fake_get_model)
    
    scraped_text = "Cafe Deluxe serves artisan coffee and pastries."
    result = extract_business_info(scraped_text)
    
    assert result["business_name"] == "Cafe Deluxe"
    assert result["industry"] == "Restaurant / Café"
    assert result["key_customers"] == "Coffee lovers and breakfast enthusiasts."
