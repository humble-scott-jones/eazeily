import sqlite3
import uuid

import app as togetherly_app


def _create_user(client, email: str, tier: str = 'team', is_admin: bool = False) -> str:
    """Signup a user through the API, then promote to the requested tier."""
    password = f"Pass-{uuid.uuid4()}"
    resp = client.post('/api/signup', json={'email': email, 'password': password})
    assert resp.status_code == 200, resp.get_data(as_text=True)

    con = sqlite3.connect(togetherly_app.DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute('SELECT id FROM users WHERE email = ?', (email.lower(),)).fetchone()
    assert row is not None
    con.execute(
        'UPDATE users SET subscription_tier = ?, is_paid = 1, is_admin = ? WHERE id = ?',
        (tier, 1 if is_admin else 0, row['id']),
    )
    con.commit()
    con.close()
    return row['id']


def _login_session(client, user_id: str) -> None:
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['profile_id'] = user_id


def test_team_approvals_flow_create_list_transition(client):
    user_id = _create_user(client, 'team-approver@example.com')
    _login_session(client, user_id)

    resp = client.get('/api/team/approvals')
    assert resp.status_code == 200
    assert resp.get_json()['approvals'] == []

    payload = {
        'title': 'Launch Reel Review',
        'content_ref': 'planner://post/abc123',
        'reviewers': ['alex@example.com'],
        'note': 'Needs a final approval today.',
    }
    resp = client.post('/api/team/approvals', json=payload)
    assert resp.status_code == 200
    created = resp.get_json()['approval']
    assert created['state'] == 'pending'
    assert created['title'] == payload['title']
    assert created['reviewers'] == payload['reviewers']

    list_resp = client.get('/api/team/approvals')
    listed_ids = [a['id'] for a in list_resp.get_json()['approvals']]
    assert created['id'] in listed_ids

    transition = client.post(f"/api/team/approvals/{created['id']}/transition", json={'action': 'approve'})
    assert transition.status_code == 200
    data = transition.get_json()
    assert data['approval']['state'] == 'approved'
    assert data['events'][0]['action'] == 'approve'
    assert any(evt['action'] == 'created' for evt in data['events'])


def test_team_approvals_requires_team_plan(client):
    user_id = _create_user(client, 'creator-only@example.com', tier='creator')
    _login_session(client, user_id)

    resp = client.get('/api/team/approvals')
    assert resp.status_code == 403

    resp = client.post('/api/team/approvals', json={'title': 'Test', 'content_ref': 'ref'})
    assert resp.status_code == 403


def test_team_approvals_create_validates_required_fields(client):
    user_id = _create_user(client, 'team-validation@example.com')
    _login_session(client, user_id)

    resp = client.post('/api/team/approvals', json={'title': '', 'content_ref': ''})
    assert resp.status_code == 400
    assert 'Title is required' in resp.get_json()['error']

    resp = client.post('/api/team/approvals', json={'title': 'Needs content ref', 'content_ref': ''})
    assert resp.status_code == 400
    assert 'content_ref is required' in resp.get_json()['error']
