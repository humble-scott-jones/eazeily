"""Tests for review response generator API."""


def test_review_response_requires_text(client):
    """Test that review response API requires review text."""
    # Create and login user
    client.post('/api/signup', json={'email': 'review@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'review@example.com', 'password': 'test123'})
    
    r = client.post('/api/generate-review-response', json={})
    assert r.status_code == 400
    j = r.get_json()
    assert j['ok'] is False
    assert 'required' in j['error'].lower()


def test_review_response_empty_text(client):
    """Test that review response API rejects empty review text."""
    # Create and login user
    client.post('/api/signup', json={'email': 'review2@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'review2@example.com', 'password': 'test123'})
    
    r = client.post('/api/generate-review-response', json={'review_text': ''})
    assert r.status_code == 400
    j = r.get_json()
    assert j['ok'] is False


def test_review_response_positive_review(client):
    """Test generating response for positive review."""
    # Create and login user
    client.post('/api/signup', json={'email': 'review3@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'review3@example.com', 'password': 'test123'})
    
    review = "Great service! The team was very professional and helpful. Highly recommend!"
    r = client.post('/api/generate-review-response', json={
        'review_text': review,
        'tone': 'professional'
    })
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'response' in j
    assert len(j['response']) > 0
    assert 'method' in j


def test_review_response_negative_review(client):
    """Test generating response for negative review."""
    # Create and login user
    client.post('/api/signup', json={'email': 'review4@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'review4@example.com', 'password': 'test123'})
    
    review = "Terrible experience. Very disappointed with the service. Never coming back."
    r = client.post('/api/generate-review-response', json={
        'review_text': review,
        'tone': 'apologetic'
    })
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'response' in j
    assert len(j['response']) > 0
    assert 'sorry' in j['response'].lower() or 'apolog' in j['response'].lower()


def test_review_response_neutral_review(client):
    """Test generating response for neutral review."""
    # Create and login user
    client.post('/api/signup', json={'email': 'review5@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'review5@example.com', 'password': 'test123'})
    
    review = "Service was okay. Nothing special but got the job done."
    r = client.post('/api/generate-review-response', json={
        'review_text': review,
        'tone': 'professional'
    })
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'response' in j
    assert len(j['response']) > 0


def test_review_response_with_company_name(client):
    """Test generating response with company name."""
    # Create and login user
    client.post('/api/signup', json={'email': 'review6@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'review6@example.com', 'password': 'test123'})
    
    review = "Great service from the team!"
    r = client.post('/api/generate-review-response', json={
        'review_text': review,
        'tone': 'grateful',
        'company_name': 'Acme Corp'
    })
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'response' in j
    if j.get('method') == 'template':
        assert 'Acme Corp' in j['response']


def test_review_response_different_tones(client):
    """Test that different tones produce different responses."""
    # Create and login user
    client.post('/api/signup', json={'email': 'review7@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'review7@example.com', 'password': 'test123'})
    
    review = "Nice experience overall."

    tones = ['professional', 'grateful', 'apologetic', 'friendly']
    responses = []

    for tone in tones:
        r = client.post('/api/generate-review-response', json={
            'review_text': review,
            'tone': tone
        })
        assert r.status_code == 200
        j = r.get_json()
        assert j['ok'] is True
        responses.append(j['response'])

    unique_responses = set(responses)
    assert len(unique_responses) >= 2


def test_review_response_sentiment_detection(client):
    """Test sentiment detection in template-based responses."""
    # Create and login user
    client.post('/api/signup', json={'email': 'review8@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'review8@example.com', 'password': 'test123'})
    
    positive_review = "Amazing service! Love it!"
    negative_review = "Worst experience ever. Terrible!"

    r1 = client.post('/api/generate-review-response', json={
        'review_text': positive_review,
        'tone': 'professional'
    })
    r2 = client.post('/api/generate-review-response', json={
        'review_text': negative_review,
        'tone': 'professional'
    })

    j1 = r1.get_json()
    j2 = r2.get_json()

    assert j1['ok'] is True
    assert j2['ok'] is True

    if j1.get('method') == 'template':
        assert 'detected_sentiment' in j1
        assert j1['detected_sentiment'] == 'positive'

    if j2.get('method') == 'template':
        assert 'detected_sentiment' in j2
        assert j2['detected_sentiment'] == 'negative'


def test_review_response_house_host_industry(client):
    """Test that house host industry gets tailored responses."""
    # Create and login user
    client.post('/api/signup', json={'email': 'host@example.com', 'password': 'test123'})
    client.post('/api/login', json={'email': 'host@example.com', 'password': 'test123'})
    
    # Test positive review response with house_host industry specified
    review = "Amazing stay! The property was clean, cozy, and had great amenities. Highly recommend!"
    r = client.post('/api/generate-review-response', json={
        'review_text': review,
        'tone': 'grateful',
        'industry': 'house_host',
        'company_name': 'Sunny Stay Vacation Rentals'
    })
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'response' in j
    # Should include company name and hospitality-specific language
    response_text = j['response']
    assert 'Sunny Stay Vacation Rentals' in response_text
    # Check for hospitality-specific language that indicates house_host templates were used
    assert 'welcome' in response_text.lower() or 'stay' in response_text.lower() or 'property' in response_text.lower()
