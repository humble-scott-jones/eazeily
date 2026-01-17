"""Tests for scraper_service.py"""
import json
from services.scraper_service import extract_business_info


def test_extract_business_info_with_ai(monkeypatch):
    """Test extract_business_info function with mocked AI."""
    
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
                    "niche_keywords": ["automation", "workflow"]
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
    assert result["key_offer"] == "Free 30-day trial with no credit card required"
    assert result["brand_keywords"] == ["innovative", "efficient"]
    assert result["niche_keywords"] == ["automation", "workflow"]
    sections = result["required_sections"]
    assert sections["basic_information"]["status"] == "ok"
    assert "Tech Startup Inc" in sections["basic_information"]["name"]
    assert sections["target_audience"]["status"] in ("ok", "missing")  # AI fills key_customers
    assert "fill_rate" in result["validation"]


def test_extract_business_info_without_ai(monkeypatch):
    """Test extract_business_info when AI is unavailable."""
    
    # Mock AI service to return None
    monkeypatch.setattr('services.ai_service.get_generative_model', lambda: None)
    
    scraped_text = "Some business content"
    result = extract_business_info(scraped_text)
    
    # Legacy fields fall back to heuristics but remain safe defaults
    assert "required_sections" in result
    assert result["required_sections"]["basic_information"]["status"] in ("ok", "missing")
    # Brand keywords may be inferred even without AI
    assert isinstance(result["brand_keywords"], list)
    assert "missing_sections" in result["validation"]


def test_extract_business_info_handles_json_error(monkeypatch):
    """Test extract_business_info handles invalid JSON from AI."""
    
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
    
    # Should return safe defaults when JSON parsing fails
    assert "required_sections" in result
    assert result["required_sections"]["basic_information"]["status"] in ("ok", "missing")


def test_extract_business_info_strips_markdown(monkeypatch):
    """Test that extract_business_info strips markdown code blocks from AI response."""
    
    # Mock the AI model to return JSON wrapped in markdown
    class FakeModel:
        def generate_content(self, prompt):
            class FakeResponse:
                text = '''```json
{
    "business_name": "Cafe Deluxe",
    "industry": "Restaurant / Café",
    "key_customers": "Coffee lovers and breakfast enthusiasts.",
    "key_offer": "Buy one coffee, get one free every Monday",
    "brand_keywords": ["artisan", "cozy"],
    "niche_keywords": ["specialty coffee", "breakfast"]
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
    assert result["key_offer"] == "Buy one coffee, get one free every Monday"
