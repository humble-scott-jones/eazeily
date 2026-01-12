import pytest

from services.scraper_service import extract_business_info


def test_required_sections_populated_from_heuristics(monkeypatch):
    """Scraper should populate required sections even without AI."""

    # Disable AI to exercise rule-based extraction
    monkeypatch.setattr("services.ai_service.get_generative_model", lambda: None)

    scraped_text = (
        "Acme Fitness helps busy professionals and teams of 10-50 get healthy. "
        "Built for remote teams and designed for founders. "
        "Pricing is transparent and you can sign up to get started. "
        "Learn how it works and get ongoing support from our coaches."
    )

    result = extract_business_info(scraped_text, url="https://acmefit.com")
    sections = result["required_sections"]

    assert sections["basic_information"]["status"] == "ok"
    assert sections["target_audience"]["status"] == "ok"
    assert sections["key_offer"]["status"] == "ok"
    assert sections["brand_keywords"]["status"] == "ok"
    assert sections["content_goals"]["status"] == "ok"
    assert len(sections["brand_keywords"]["values"]) <= 10
    assert "missing_sections" in result["validation"]
    assert result["validation"]["fill_rate"] == pytest.approx(1.0)


def test_missing_sections_surface_reason(monkeypatch):
    """Missing fields should report a reason instead of silently dropping."""

    monkeypatch.setattr("services.ai_service.get_generative_model", lambda: None)
    result = extract_business_info("", url="")
    sections = result["required_sections"]

    for payload in sections.values():
        assert payload["status"] == "missing"
        assert payload["missing_reason"]
    assert result["validation"]["fill_rate"] == 0
