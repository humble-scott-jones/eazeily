"""Tests for admin dashboard user listing endpoint."""


def test_admin_users_requires_auth(client, monkeypatch):
    """Test that /api/admin/users requires admin authentication."""
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'password123'})
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')

    r = client.get('/api/admin/users')
    assert r.status_code == 403
    j = r.get_json()
    assert j['ok'] is False
    assert 'Admin required' in j['error']


def test_admin_users_list(client, monkeypatch):
    """Test that admin users endpoint returns user list."""
    client.post('/api/signup', json={'email': 'user1@example.com', 'password': 'password123'})
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'user2@example.com', 'password': 'password123'})
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'password123'})

    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'password123'})

    r = client.get('/api/admin/users')
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'users' in j
    assert 'stats' in j
    assert j['stats']['total_users'] >= 3
    assert len(j['users']) >= 3

    user = j['users'][0]
    assert 'id' in user
    assert 'email' in user
    assert 'is_paid' in user
    assert 'created_at' in user


def test_admin_users_stats(client, monkeypatch):
    """Test that admin users endpoint returns correct stats."""
    r1 = client.post('/api/signup', json={'email': 'paid@example.com', 'password': 'password123'})
    user1_id = r1.get_json()['id']

    with client.application.app_context():
        from app import get_db
        db = get_db()
        db.execute('UPDATE users SET is_paid = 1 WHERE id = ?', (user1_id,))
        db.commit()

    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'free@example.com', 'password': 'password123'})
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'password123'})

    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'password123'})

    r = client.get('/api/admin/users')
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert j['stats']['total_users'] >= 3
    assert j['stats']['paid_users'] >= 1
    assert j['stats']['free_users'] >= 2


def test_admin_page_access(client, monkeypatch):
    """Test that admin page is accessible only to admins."""
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'password123'})

    r = client.get('/admin')
    assert r.status_code == 200
    assert b'not authorized' in r.data.lower()

    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'password123'})
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')

    r = client.get('/admin')
    assert r.status_code == 200
    assert b'Admin Dashboard' in r.data or b'Admin' in r.data
