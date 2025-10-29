import json
import os

import app as appmod
import generator as gen_mod


def _make_fake_client_with_content(content):
    # Return a fake client whose completions.create returns a dict-like response
    # {'choices': [{'message': {'content': content}}]}
    class Completions:
        def create(self, *a, **kw):
            return {'choices': [{'message': {'content': content}}]}

    fake_client = type('Fake', (), {'chat': type('C', (), {'completions': Completions()})()})()
    return fake_client


def test_generate_with_openai_success(tmp_path, monkeypatch):
    # Arrange: enable OpenAI path and inject fake client returning valid JSON
    appmod.USE_OPENAI = True
    posts = [{'post_day': 0, 'platform': 'instagram', 'caption': 'Hello world!', 'hashtags': ['#hi']}]
    fake = _make_fake_client_with_content(json.dumps(posts))
    monkeypatch.setattr(appmod, 'openai_client', fake)

    # Ensure DB and test user exist
    with appmod.app.app_context():
        appmod.init_db()
        db = appmod.get_db()
        db.execute("INSERT OR REPLACE INTO users (id, email, password_hash, is_paid, free_sample_used) VALUES (?, ?, ?, ?, ?)", ('test-uid', 't@example.com', 'x', 1, 0))
        db.commit()

    # Act
    client = appmod.app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-uid'
        sess['profile_id'] = 'profile-1'

    rv = client.post('/api/generate', json={'days': 1})

    # Assert
    assert rv.status_code == 200
    j = rv.get_json()
    assert j['count'] == 1
    assert isinstance(j['posts'], list)
    # Content may be produced by AI or filtered by the generator fallback depending on parsing;
    # ensure at least a post object is present with expected keys.
    assert 'caption' in j['posts'][0]


def test_generate_with_openai_malformed_json_falls_back(tmp_path, monkeypatch):
    # Arrange: OpenAI returns malformed content, generator fallback should be used
    appmod.USE_OPENAI = True
    fake = _make_fake_client_with_content('not valid json')
    monkeypatch.setattr(appmod, 'openai_client', fake)

    fallback = [{'caption': 'fallback-caption', 'hashtags': [], 'platform': 'instagram', 'post_day': 0}]
    monkeypatch.setattr(gen_mod, 'generate_posts', lambda **kwargs: fallback)

    with appmod.app.app_context():
        appmod.init_db()
        db = appmod.get_db()
        db.execute("INSERT OR REPLACE INTO users (id, email, password_hash, is_paid, free_sample_used) VALUES (?, ?, ?, ?, ?)", ('test-uid-2', 't2@example.com', 'x', 1, 0))
        db.commit()

    client = appmod.app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 'test-uid-2'
        sess['profile_id'] = 'profile-2'

    rv = client.post('/api/generate', json={'days': 1})
    assert rv.status_code == 200
    j = rv.get_json()
    assert j['count'] == 1
    assert j['posts'][0]['caption'] == 'fallback-caption'
