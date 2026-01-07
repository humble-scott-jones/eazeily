import pytest
import uuid

from models import db, User
from routes import generate_routes


@pytest.fixture
def authed_client(client):
    # Create a user and log them in via session
    with client.application.app_context():
        user = User()
        user.email = f"tester_{uuid.uuid4().hex}@example.com"
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        user_id = user.id

    with client.session_transaction() as sess:
        sess['_user_id'] = str(user_id)

    return client


def _mock_generate(monkeypatch):
    def _fake_generate(profile, topic, task_type, platform=None):
        return f"{task_type}:{platform or ''}:{topic}"

    monkeypatch.setattr(generate_routes.voice_engine, "generate_expert_content", _fake_generate)


def test_unknown_task_type_returns_400(authed_client, monkeypatch):
    monkeypatch.setenv("GENAI_API_KEY", "test-key")
    _mock_generate(monkeypatch)

    resp = authed_client.post('/api/generate', json={
        "task_type": "unknown",
        "topic": "test"
    })

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["status"] == "error"
    assert body["error"]["code"] == "invalid_task_type"
    assert "allowed" in body["error"]


def test_missing_topic_returns_400(authed_client, monkeypatch):
    monkeypatch.setenv("GENAI_API_KEY", "test-key")
    _mock_generate(monkeypatch)

    resp = authed_client.post('/api/generate', json={
        "task_type": "post",
        "platform": "LinkedIn"
    })

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"]["code"] == "missing_topic"


def test_post_requires_platform(authed_client, monkeypatch):
    monkeypatch.setenv("GENAI_API_KEY", "test-key")
    _mock_generate(monkeypatch)

    resp = authed_client.post('/api/generate', json={
        "task_type": "post",
        "topic": "Summer sale"
    })

    assert resp.status_code == 400
    body = resp.get_json()
    assert body["error"]["code"] == "platform_required"


def test_successful_generation_with_alias_route(authed_client, monkeypatch):
    monkeypatch.setenv("GENAI_API_KEY", "test-key")
    _mock_generate(monkeypatch)

    resp = authed_client.post('/api/generate/post', json={
        "topic": "Grand opening",
        "platform": "Instagram"
    })

    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "success"
    assert "content" in body
