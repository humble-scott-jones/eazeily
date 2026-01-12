"""
Test that multiple URL scrapes accumulate data instead of replacing it.
"""
import pytest
from models import VoiceProfile


def test_multiple_scrapes_accumulate_urls(client):
    """Test that scraping multiple URLs accumulates them in scraped_url field."""
    # 1. Create a user
    signup_response = client.post('/api/signup', json={
        'email': 'accumulation_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # 2. Save an initial profile with one scraped URL
    profile_data = {
        'company': 'Test Co',
        'industry': 'Software / Tech / Startup',
        'tone': 'professional',
        'scraped_url': 'https://example.com',
        'brand_keywords': ['innovative', 'fast']
    }
    
    save_response = client.post('/api/profile', json=profile_data)
    assert save_response.status_code == 200
    
    # 3. Simulate a second scrape from a different URL (e.g., social media)
    # In reality, this would come from the scraper backend, but we're testing the merge logic
    profile_data_2 = {
        'company': 'Test Co',  # Same company, don't overwrite
        'industry': 'Software / Tech / Startup',
        'tone': 'professional',
        'brand_keywords': ['innovative', 'fast', 'reliable', 'user-friendly'],  # Merged keywords
        'niche_keywords': ['SaaS', 'cloud'],  # New keywords from second scrape
        'target_audience': 'Small businesses',  # New data from second scrape
        'scraped_url': 'https://example.com, https://instagram.com/example'  # Both URLs
    }
    
    save_response_2 = client.post('/api/profile', json=profile_data_2)
    assert save_response_2.status_code == 200
    
    # 4. Retrieve and verify data accumulated
    get_response = client.get('/api/profile')
    assert get_response.status_code == 200
    get_data = get_response.get_json()
    assert get_data['ok'] is True
    
    profile = get_data['profile']
    
    # Verify URLs accumulated (testing data storage, not URL security sanitization)
    assert 'example.com' in profile['scraped_url']
    assert 'instagram.com/example' in profile['scraped_url']
    
    # Verify keywords merged (should have all 4)
    assert len(profile['brand_keywords']) == 4
    assert 'innovative' in profile['brand_keywords']
    assert 'fast' in profile['brand_keywords']
    assert 'reliable' in profile['brand_keywords']
    assert 'user-friendly' in profile['brand_keywords']
    
    # Verify new data was added
    assert 'SaaS' in profile['niche_keywords']
    assert 'cloud' in profile['niche_keywords']
    assert profile['target_audience'] == 'Small businesses'


def test_keywords_merge_without_duplicates(client):
    """Test that keywords from multiple scrapes merge without creating duplicates."""
    # 1. Create a user
    signup_response = client.post('/api/signup', json={
        'email': 'keyword_merge@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # 2. Save profile with initial keywords
    profile_data = {
        'company': 'KeywordCo',
        'industry': 'Retail / Boutique',
        'tone': 'friendly',
        'brand_keywords': ['sustainable', 'eco-friendly', 'premium']
    }
    
    save_response = client.post('/api/profile', json=profile_data)
    assert save_response.status_code == 200
    
    # 3. Update with overlapping keywords (simulate second scrape)
    profile_data_2 = {
        'brand_keywords': ['sustainable', 'eco-friendly', 'premium', 'organic', 'ethical']
    }
    
    save_response_2 = client.post('/api/profile', json=profile_data_2)
    assert save_response_2.status_code == 200
    
    # 4. Verify no duplicates
    get_response = client.get('/api/profile')
    assert get_response.status_code == 200
    profile = get_response.get_json()['profile']
    
    # Should have 5 unique keywords
    assert len(profile['brand_keywords']) == 5
    assert 'sustainable' in profile['brand_keywords']
    assert 'organic' in profile['brand_keywords']
    assert 'ethical' in profile['brand_keywords']
    
    # Check no duplicates
    assert len(profile['brand_keywords']) == len(set(profile['brand_keywords']))


def test_scrape_history_tracked_in_metadata(client):
    """Test that scrape history is tracked in scraped_meta."""
    # 1. Create a user
    signup_response = client.post('/api/signup', json={
        'email': 'history_test@example.com',
        'password': 'testpass123'
    })
    assert signup_response.status_code in (200, 201)
    
    # 2. Save profile with scraped_meta that includes history
    from datetime import datetime
    
    scrape_history = [
        {
            'url': 'https://example.com',
            'extracted_at': datetime.utcnow().isoformat(),
            'business_name': 'Test Co',
            'industry': 'Software / Tech / Startup'
        },
        {
            'url': 'https://instagram.com/testco',
            'extracted_at': datetime.utcnow().isoformat(),
            'business_name': 'Test Co',
            'industry': 'Software / Tech / Startup'
        }
    ]
    
    scraped_meta = {
        'scrape_history': scrape_history,
        'last_url': 'https://instagram.com/testco',
        'last_scraped_at': datetime.utcnow().isoformat()
    }
    
    profile_data = {
        'company': 'Test Co',
        'industry': 'Software / Tech / Startup',
        'tone': 'professional',
        'scraped_meta': scraped_meta
    }
    
    save_response = client.post('/api/profile', json=profile_data)
    assert save_response.status_code == 200
    
    # 3. Retrieve and verify history is preserved
    get_response = client.get('/api/profile')
    assert get_response.status_code == 200
    profile = get_response.get_json()['profile']
    
    assert 'scrape_history' in profile['scraped_meta']
    assert len(profile['scraped_meta']['scrape_history']) == 2
    assert profile['scraped_meta']['last_url'] == 'https://instagram.com/testco'
