import pytest

pytest.skip("OpenAI path removed; Gemini-only stack", allow_module_level=True)

import generator as gen_mod


def test_generate_openai_failure_uses_fallback(monkeypatch, client):
    gen_mod.USE_OPENAI_FOR_POSTS = True

    class BoomCompletions:
        def create(self, *args, **kwargs):
            raise RuntimeError('boom')

    gen_mod._openai_client = type('Fake', (), {'chat': type('C', (), {'completions': BoomCompletions()})()})()

    fallback_posts = [{'caption': 'fallback', 'platform': 'instagram'}]
    monkeypatch.setattr(gen_mod, 'generate_posts', lambda **kwargs: fallback_posts)

    with client.session_transaction() as sess:
        sess['profile_id'] = 'openai-fallback'

    resp = client.post('/api/generate', json={'days': 1})
    assert resp.status_code == 200

    body = resp.get_json()
    assert body['ok'] is True
    assert body['posts'][0]['caption'] == 'fallback'
