"""
Test that content_goals are extracted and returned by the website analyzer.
This validates the fix for: "Brand keywords and goals and target audience is not 
populating in profile text boxes when analyzing the website."
"""
import pytest


def _extract_goal_types(goals):
    """Helper to extract unique goal types from goal objects."""
    return list(set(g.get('goal') for g in goals if isinstance(g, dict) and g.get('goal')))


def test_onboarding_social_style_returns_content_goals(monkeypatch, client):
    """Test that the /onboarding/social-style endpoint returns content_goals in suggestions."""
    # Login first
    resp = client.post('/auth/signup', json={'email': 'goaltest@example.com', 'password': 'secret123'})
    assert resp.status_code in (200, 201, 400)  # 400 if user already exists
    resp = client.post('/auth/login', json={'email': 'goaltest@example.com', 'password': 'secret123'})
    assert resp.status_code == 200
    
    # Mock the scraper service
    sample_text = """
    Learn more about our fitness programs. Sign up today for a free consultation!
    We help busy professionals achieve their health goals. Book your appointment now.
    Get started with personalized training plans.
    """
    
    def mock_scrape_url(url, max_length=6000):
        return sample_text
    
    def mock_extract_business_info(scraped_text, url=""):
        # Simulate what the real function returns, including content_goals
        from services.scraper_service import _extract_content_goals
        content_goals = _extract_content_goals(scraped_text)
        
        return {
            "business_name": "FitLife Gym",
            "industry": "Fitness / Wellness",
            "key_customers": "Busy professionals looking to improve their health",
            "key_offer": "Free consultation and personalized training",
            "brand_keywords": ["innovative", "personalized", "results-driven"],
            "niche_keywords": ["fitness", "personal training", "health coaching"],
            "required_sections": {
                "basic_information": {
                    "name": "FitLife Gym",
                    "description": "Your Journey to Better Health",
                    "website": url,
                    "industry": "Fitness / Wellness"
                },
                "target_audience": {
                    "values": ["Busy professionals", "Health-conscious individuals"]
                },
                "key_offer": {
                    "headline": "Free consultation",
                    "value_prop": "Personalized training plans"
                },
                "brand_keywords": {
                    "values": ["innovative", "personalized", "results-driven"]
                },
                "content_goals": {
                    "values": content_goals,
                    "status": "ok" if content_goals else "missing"
                }
            },
            "validation": {
                "missing_sections": [],
                "fill_rate": 1.0
            },
            "target_audience": ["Busy professionals", "Health-conscious individuals"]
        }
    
    monkeypatch.setattr('services.scraper_service.scrape_url', mock_scrape_url)
    monkeypatch.setattr('services.scraper_service.extract_business_info', mock_extract_business_info)
    
    # Make request to social-style endpoint
    resp = client.post('/onboarding/social-style', json={
        'url': 'https://fitlifegym.com',
        'consent': True,
        'business_name': 'FitLife'
    })
    
    assert resp.status_code == 200
    data = resp.get_json()
    
    # Verify response structure
    assert 'suggestions' in data
    assert 'source' in data
    assert data['source'] == 'website'
    
    suggestions = data['suggestions']
    
    # Verify all key fields are present
    assert suggestions['business_name'] == 'FitLife Gym'
    assert suggestions['industry'] == 'Fitness / Wellness'
    assert suggestions['key_customers'] == 'Busy professionals looking to improve their health'
    assert suggestions['key_offer'] == 'Free consultation and personalized training'
    assert 'innovative' in suggestions['brand_keywords']
    assert 'niche_keywords' in suggestions
    
    # THE KEY TEST: Verify content_goals are returned
    assert 'content_goals' in suggestions, "content_goals should be in suggestions"
    assert isinstance(suggestions['content_goals'], list), "content_goals should be a list"
    assert len(suggestions['content_goals']) > 0, "content_goals should not be empty"
    
    # Verify the goals make sense based on the sample text
    # Sample text has: "learn" (awareness), "sign up" (lead_gen), "help" (retention)
    goals = suggestions['content_goals']
    assert 'awareness/education' in goals, "Should detect 'learn' keyword for awareness/education"
    assert 'lead_gen/conversion' in goals, "Should detect 'sign up'/'get started' keywords"
    assert 'retention/support' in goals, "Should detect 'help' keyword"


def test_content_goals_extraction_from_keywords(client):
    """Test that _extract_content_goals correctly identifies goal keywords in text."""
    from services.scraper_service import _extract_content_goals
    
    # Test awareness/education keywords
    text1 = "Learn how to improve your skills. Discover our educational programs."
    goals1 = _extract_content_goals(text1)
    goal_types1 = _extract_goal_types(goals1)
    assert 'awareness/education' in goal_types1
    
    # Test lead_gen/conversion keywords
    text2 = "Sign up today! Get started now. Book your free consultation."
    goals2 = _extract_content_goals(text2)
    goal_types2 = _extract_goal_types(goals2)
    assert 'lead_gen/conversion' in goal_types2
    
    # Test retention/support keywords
    text3 = "Need help? Check our FAQ and customer support resources."
    goals3 = _extract_content_goals(text3)
    goal_types3 = _extract_goal_types(goals3)
    assert 'retention/support' in goal_types3
    
    # Test mixed keywords
    text4 = "Learn more about our services. Sign up for a demo. We're here to help."
    goals4 = _extract_content_goals(text4)
    goal_types4 = _extract_goal_types(goals4)
    # The helper function deduplicates, so we check for at least 3 unique types
    # (could be exactly 3 or more if additional goal types are detected)
    assert len(goal_types4) >= 3, "Should find at least three unique goal types"
    assert 'awareness/education' in goal_types4
    assert 'lead_gen/conversion' in goal_types4
    assert 'retention/support' in goal_types4
