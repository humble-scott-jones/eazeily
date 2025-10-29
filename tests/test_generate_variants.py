import importlib
import os


def test_generate_variants_fallback(monkeypatch):
    # Ensure development mode so endpoint allows unauthenticated sampling
    monkeypatch.setenv('FLASK_ENV', 'development')
    # reload app module so it picks up env change
    import app as togetherly_app
    importlib.reload(togetherly_app)
    # ensure OpenAI path is disabled for deterministic behavior in tests
    togetherly_app.USE_OPENAI = False

    client = togetherly_app.app.test_client()
    resp = client.post('/api/generate-variants', json={
        'industry': 'bakery',
        'platform': 'instagram',
        'tone': 'friendly',
        'count': 3
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert data and data.get('ok') is True
    assert 'variants' in data
    assert len(data['variants']) == 3


def test_generate_variants_requires_auth_in_prod(monkeypatch):
    # In production, endpoint should require authentication
    monkeypatch.setenv('FLASK_ENV', 'production')
    import app as togetherly_app
    importlib.reload(togetherly_app)
    togetherly_app.USE_OPENAI = False

    client = togetherly_app.app.test_client()
    resp = client.post('/api/generate-variants', json={
        'industry': 'bakery',
        'platform': 'instagram',
        'tone': 'friendly',
        'count': 1
    })
    assert resp.status_code == 401
