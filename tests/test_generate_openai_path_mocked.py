import json

import generator as gen_mod


def _fake_openai_with_content(content: str):
    class Completions:
        def create(self, *args, **kwargs):
            return {'choices': [{'message': {'content': content}}]}

    return type('Fake', (), {'chat': type('C', (), {'completions': Completions()})()})()


def test_generate_openai_path_parses_payload(monkeypatch, client):
    gen_mod.USE_OPENAI_FOR_POSTS = True
    gen_mod._openai_client = _fake_openai_with_content(json.dumps([
        {'caption': 'from-openai', 'pillar': 'launch', 'image_prompt': 'image'}
    ]))

    with client.session_transaction() as sess:
        sess['profile_id'] = 'openai-mock'

    resp = client.post('/api/generate', json={'days': 1})
    assert resp.status_code == 200

    body = resp.get_json()
    assert body['ok'] is True
    assert body['posts'][0]['caption'] == 'from-openai'
    assert body.get('request_id')
