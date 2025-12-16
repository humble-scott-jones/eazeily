import app


def test_profile_load_failure_returns_error_json(monkeypatch, client):
    def boom():
        raise RuntimeError('db unavailable')

    monkeypatch.setattr(app, 'get_db', boom)
    resp = client.get('/api/profile')
    assert resp.status_code == 500
    data = resp.get_json()
    assert data.get('ok') is False
    assert data.get('request_id')
    assert data.get('error', {}).get('message')
