import app


def test_generate_social_handles_upstream_failure(client, monkeypatch):
    def boom(_payload):
        raise RuntimeError('upstream failed')

    monkeypatch.setattr(app, '_generate_posts_via_openai', boom)

    resp = client.post('/api/generate/social', json={
        'platforms': ['instagram'],
        'goals': 'Resilient planning',
        'days': 1,
    })
    body = resp.get_json()
    assert resp.status_code == 200
    assert body['ok'] is True
    assert body['data']['posts']
    assert body['request_id']
