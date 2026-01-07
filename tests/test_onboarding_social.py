import json


def _login(client):
    resp = client.post('/auth/signup', json={'email': 'aihelper@example.com', 'password': 'secret123'})
    assert resp.status_code in (200, 201, 400)
    resp = client.post('/auth/login', json={'email': 'aihelper@example.com', 'password': 'secret123'})
    assert resp.status_code == 200


def test_social_style_requires_consent(client):
    _login(client)
    resp = client.post('/onboarding/social-style', json={
        'url': 'https://instagram.com/testprofile',
        'consent': False
    })
    assert resp.status_code == 400
    assert b"Consent is required" in resp.data


def test_social_style_website_primary(monkeypatch, client):
    _login(client)

    class FakeResponse:
        status_code = 200
        text = """
        <html><head><meta property='og:description' content='We help people #win big 🏆'></head>
        <body>
        <p>Feeling great today! 🚀 Launching new products.</p>
        <p>Another day, another #growth story. Stay tuned! 💡 #founderlife</p>
        </body></html>
        """

        def raise_for_status(self):
            return None

    def fake_get(url, headers=None, timeout=10):
        return FakeResponse()

    # Website should provide full suggestions
    monkeypatch.setattr('services.scraper_service.scrape_url', lambda url, max_length=6000: "We build bold products. Our offer: free strategy call. No fluff.")

    resp = client.post('/onboarding/social-style', json={
        'url': 'https://example.com',
        'consent': True,
        'business_name': 'TestCo'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['source'] == 'website'
    assert data['suggestions']['brand_voice']
    assert data['suggestions']['voice_rules']


def test_social_style_social_only(monkeypatch, client):
    _login(client)

    class FakeResponse:
        status_code = 200
        text = """
        <html><body>
        <p>Fun day! 🎉 Join us at 6pm. #party</p>
        <p>Another win for the team! �</p>
        </body></html>
        """

        def raise_for_status(self):
            return None

    monkeypatch.setattr('routes.onboarding_routes.requests.get', lambda url, headers=None, timeout=10: FakeResponse())

    resp = client.post('/onboarding/social-style', json={
        'url': 'https://www.instagram.com/testprofile',
        'consent': True,
        'business_name': 'TestCo'
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['source'] == 'social'
    assert data['suggestions']['sample_copy']
    assert data['suggestions']['brand_voice'] is None