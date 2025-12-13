import app


def test_generate_social_valid_payload_returns_posts(client):
    payload = {
        'platforms': ['instagram', 'facebook'],
        'goals': 'Announce our launch',
        'days': 2,
        'keywords': ['launch', 'ai'],
    }
    resp = client.post('/api/generate/social', json=payload)
    body = resp.get_json()
    assert resp.status_code == 200
    assert body['ok'] is True
    assert body['request_id']
    assert body['data']['posts']
    assert len(body['data']['posts']) >= 2


def test_generate_social_invalid_payload_has_error(client):
    payload = {'platforms': [], 'goals': '', 'days': 0}
    resp = client.post('/api/generate/social', json=payload)
    body = resp.get_json()
    assert resp.status_code == 400
    assert body['ok'] is False
    assert body['error']['code']
    assert body['request_id']
