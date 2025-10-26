import json


def test_admin_list_users(client, monkeypatch):
    """Test that admin can list all users."""
    # Create test users
    client.post('/api/signup', json={'email': 'user1@example.com', 'password': 'pass123'})
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'user2@example.com', 'password': 'pass123'})
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Set admin email
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    
    # Login as admin
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # List users
    r = client.get('/api/admin/users')
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'users' in j
    assert len(j['users']) >= 3
    
    # Verify user data structure
    user = j['users'][0]
    assert 'id' in user
    assert 'email' in user
    assert 'is_paid' in user
    assert 'created_at' in user


def test_admin_list_users_requires_admin(client):
    """Test that non-admin users cannot list users."""
    # Create and login as regular user
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'pass123'})
    
    # Try to list users (should fail)
    r = client.get('/api/admin/users')
    assert r.status_code == 403
    j = r.get_json()
    assert j['ok'] is False


def test_admin_reset_user_password(client, monkeypatch):
    """Test that admin can trigger password reset for a user."""
    # Create users
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'pass123'})
    user_id = client.get('/api/current_user').get_json()['id']
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Set admin email
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    
    # Set CSRF token
    with client.session_transaction() as sess:
        sess['admin_csrf'] = 'token123'
    
    # Login as admin
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Reset password for user
    r = client.post(f'/api/admin/users/{user_id}/reset-password', headers={'X-CSRF-Token': 'token123'})
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'token' in j
    assert 'email' in j
    assert j['email'] == 'user@example.com'


def test_admin_reset_password_requires_csrf(client, monkeypatch):
    """Test that password reset requires CSRF token."""
    # Create users
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'pass123'})
    user_id = client.get('/api/current_user').get_json()['id']
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Set admin email
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    
    # Login as admin but don't send CSRF token
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Try to reset password without CSRF token
    r = client.post(f'/api/admin/users/{user_id}/reset-password')
    assert r.status_code == 403


def test_admin_update_user(client, monkeypatch):
    """Test that admin can update user information."""
    # Create users
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'pass123'})
    user_id = client.get('/api/current_user').get_json()['id']
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Set admin email
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    
    # Set CSRF token
    with client.session_transaction() as sess:
        sess['admin_csrf'] = 'token123'
    
    # Login as admin
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Update user - make them paid
    r = client.patch(f'/api/admin/users/{user_id}', 
                     json={'is_paid': True},
                     headers={'X-CSRF-Token': 'token123'})
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert 'user' in j
    assert j['user']['is_paid'] == 1


def test_admin_update_user_email(client, monkeypatch):
    """Test that admin can update user email."""
    # Create users
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'pass123'})
    user_id = client.get('/api/current_user').get_json()['id']
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Set admin email
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    
    # Set CSRF token
    with client.session_transaction() as sess:
        sess['admin_csrf'] = 'token123'
    
    # Login as admin
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Update user email
    r = client.patch(f'/api/admin/users/{user_id}', 
                     json={'email': 'newemail@example.com'},
                     headers={'X-CSRF-Token': 'token123'})
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    assert j['user']['email'] == 'newemail@example.com'


def test_admin_update_user_requires_admin(client):
    """Test that non-admin users cannot update users."""
    # Create user
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'pass123'})
    user_id = client.get('/api/current_user').get_json()['id']
    
    # Try to update as non-admin
    r = client.patch(f'/api/admin/users/{user_id}', json={'is_paid': True})
    assert r.status_code == 403


def test_admin_delete_user(client, monkeypatch):
    """Test that admin can delete a user."""
    # Create users
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'pass123'})
    user_id = client.get('/api/current_user').get_json()['id']
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Set admin email
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    
    # Set CSRF token
    with client.session_transaction() as sess:
        sess['admin_csrf'] = 'token123'
    
    # Login as admin
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Delete user
    r = client.delete(f'/api/admin/users/{user_id}', headers={'X-CSRF-Token': 'token123'})
    assert r.status_code == 200
    j = r.get_json()
    assert j['ok'] is True
    
    # Verify user is deleted - list should not contain the user
    r = client.get('/api/admin/users')
    j = r.get_json()
    user_emails = [u['email'] for u in j['users']]
    assert 'user@example.com' not in user_emails


def test_admin_delete_user_requires_csrf(client, monkeypatch):
    """Test that delete user requires CSRF token."""
    # Create users
    client.post('/api/signup', json={'email': 'user@example.com', 'password': 'pass123'})
    user_id = client.get('/api/current_user').get_json()['id']
    client.post('/api/logout')
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Set admin email
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    
    # Login as admin but don't send CSRF token
    client.post('/api/login', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Try to delete without CSRF token
    r = client.delete(f'/api/admin/users/{user_id}')
    assert r.status_code == 403


def test_admin_delete_nonexistent_user(client, monkeypatch):
    """Test that deleting a non-existent user returns 404."""
    # Create admin
    client.post('/api/signup', json={'email': 'admin@example.com', 'password': 'pass123'})
    
    # Set admin email
    monkeypatch.setenv('ADMIN_EMAILS', 'admin@example.com')
    
    # Set CSRF token
    with client.session_transaction() as sess:
        sess['admin_csrf'] = 'token123'
    
    # Try to delete non-existent user
    r = client.delete('/api/admin/users/nonexistent-id', headers={'X-CSRF-Token': 'token123'})
    assert r.status_code == 404
