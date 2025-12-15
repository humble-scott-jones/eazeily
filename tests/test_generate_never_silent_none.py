import generator as gen_mod


def test_generate_none_payload_surfaces_error(monkeypatch, client):
    monkeypatch.setattr(gen_mod, 'USE_OPENAI_FOR_POSTS', False)
    monkeypatch.setattr(gen_mod, 'generate_posts', lambda **kwargs: None)

    with client.session_transaction() as sess:
        sess['profile_id'] = 'none-payload'

    resp = client.post('/api/generate', json={'days': 1})
    assert resp.status_code == 500

    body = resp.get_json()
    assert body['ok'] is False
    assert body['error']['message']
    assert body.get('request_id')
