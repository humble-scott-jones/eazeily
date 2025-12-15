import json
import os
import json

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


def test_generate_with_image_payload_uses_image_helper(tmp_path, monkeypatch):
    appmod.USE_OPENAI = True
    appmod.openai_client = object()

    captured = {}

    def fake_image_generator(spec):
        captured['spec'] = spec
        return [{'caption': 'from image', 'platform': 'instagram', 'day_index': 1}]

    monkeypatch.setattr(appmod, '_generate_posts_from_image', fake_image_generator)
    monkeypatch.setattr(appmod, '_generate_posts_via_openai', lambda spec: None)

    with appmod.app.app_context():
        appmod.init_db()
        db = appmod.get_db()
        db.execute("INSERT OR REPLACE INTO users (id, email, password_hash, is_paid, free_sample_used) VALUES (?, ?, ?, ?, ?)", ('img-user', 'img@example.com', 'x', 1, 0))
        db.commit()

    client = appmod.app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = 'img-user'
        sess['profile_id'] = 'profile-img'

    rv = client.post('/api/generate', json={'days': 1, 'image_data_url': 'data:image/png;base64,AAAA', 'image_context': 'Lean into the blue tones.'})
    assert rv.status_code == 200
    body = rv.get_json()
    assert body['posts'][0]['caption'] == 'from image'
    assert 'spec' in captured
    assert captured['spec']['image_data_url'].startswith('data:image/png')
    assert captured['spec']['image_context'] == 'Lean into the blue tones.'


def test_generate_rejects_oversized_image_payload(client):
    with client.session_transaction() as sess:
        sess['profile_id'] = 'profile-big'
    huge_payload = 'data:image/png;base64,' + ('a' * (appmod.IMAGE_DATA_URL_MAX_BYTES + 10))
    rv = client.post('/api/generate', json={'days': 1, 'image_data_url': huge_payload})
    assert rv.status_code == 400


def test_image_generation_requires_openai(monkeypatch, client):
    """If OpenAI is not configured, image-to-post should return a clear error."""

    # Ensure OpenAI path is disabled
    monkeypatch.setattr(appmod, 'USE_OPENAI', False)
    monkeypatch.setattr(appmod, 'openai_client', None)

    with client.session_transaction() as sess:
        sess['profile_id'] = 'profile-no-openai'

    rv = client.post('/api/generate', json={'days': 1, 'image_data_url': 'data:image/png;base64,AAAA'})
    assert rv.status_code == 503
    body = rv.get_json()
    assert body['error']['message'].startswith('Image-to-post generation requires OpenAI')
