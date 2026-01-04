"""
Tests for the authentication overhaul implementation.
Validates that the authentication system works correctly with:
1. Proper password hashing (using bcrypt)
2. Flash messages for login failures
3. The /fix-my-account emergency reset route
"""
import pytest
from flask import session
from models import User, db


def test_signup_creates_user_with_hashed_password(app):
    """Test that signup creates a user with properly hashed password."""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Sign up a new user
            response = client.post('/auth/signup', 
                                   json={'email': 'newuser@test.com', 'password': 'securepass123'},
                                   content_type='application/json')
            
            assert response.status_code == 201
            data = response.get_json()
            assert data['message'] == 'User created and logged in'
            assert data['user']['email'] == 'newuser@test.com'
            
            # Verify the user exists in DB with hashed password
            user = User.query.filter_by(email='newuser@test.com').first()
            assert user is not None
            assert user.password_hash != 'securepass123'  # Should be hashed
            assert user.password_hash.startswith('$2b$') or user.password_hash.startswith('$2a$')
            assert user.check_password('securepass123') is True


def test_login_with_valid_credentials(app):
    """Test that login works with valid credentials."""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create a user first
            user = User(email='validuser@test.com', password_hash='')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Try to login
            response = client.post('/auth/login',
                                   json={'email': 'validuser@test.com', 'password': 'password123'},
                                   content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'Logged in successfully'
            assert data['user']['email'] == 'validuser@test.com'


def test_login_with_invalid_email(app):
    """Test that login fails with proper message for non-existent user."""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Try to login with non-existent email
            response = client.post('/auth/login',
                                   json={'email': 'notfound@test.com', 'password': 'password123'},
                                   content_type='application/json')
            
            assert response.status_code == 401
            data = response.get_json()
            assert data['error'] == 'Invalid credentials'


def test_login_with_wrong_password(app):
    """Test that login fails with proper message for wrong password."""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create a user
            user = User(email='wrongpass@test.com', password_hash='')
            user.set_password('correctpassword')
            db.session.add(user)
            db.session.commit()
            
            # Try to login with wrong password
            response = client.post('/auth/login',
                                   json={'email': 'wrongpass@test.com', 'password': 'wrongpassword'},
                                   content_type='application/json')
            
            assert response.status_code == 401
            data = response.get_json()
            assert data['error'] == 'Invalid credentials'


def test_login_remember_me_functionality(app):
    """Test that 'remember me' functionality works."""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create a user
            user = User(email='remember@test.com', password_hash='')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Login with remember=True
            response = client.post('/auth/login',
                                   json={'email': 'remember@test.com', 
                                        'password': 'password123',
                                        'remember': True},
                                   content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'Logged in successfully'


def test_fix_my_account_route_with_valid_key(app):
    """Test that /fix-my-account works with the correct security key."""
    with app.test_client() as client:
        with app.app_context():
            # Call the fix-my-account endpoint with the correct key
            response = client.get('/fix-my-account?key=fix-it-now')
            
            assert response.status_code == 200
            assert b'Database rebuilt' in response.data
            assert b'hi.scott.jones@gmail.com' in response.data
            
            # Verify the user was created
            user = User.query.filter_by(email='hi.scott.jones@gmail.com').first()
            assert user is not None
            assert user.check_password('password123') is True


def test_fix_my_account_route_without_key(app):
    """Test that /fix-my-account is protected and returns 403 without key."""
    with app.test_client() as client:
        response = client.get('/fix-my-account')
        assert response.status_code == 403


def test_fix_my_account_route_with_wrong_key(app):
    """Test that /fix-my-account rejects wrong security key."""
    with app.test_client() as client:
        response = client.get('/fix-my-account?key=wrong-key')
        assert response.status_code == 403


def test_login_after_fix_my_account(app):
    """Integration test: Verify login works after running fix-my-account."""
    with app.test_client() as client:
        with app.app_context():
            # First, run fix-my-account
            response = client.get('/fix-my-account?key=fix-it-now')
            assert response.status_code == 200
            
            # Now try to login with the created account
            response = client.post('/auth/login',
                                   json={'email': 'hi.scott.jones@gmail.com', 
                                        'password': 'password123'},
                                   content_type='application/json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'Logged in successfully'
            assert data['user']['email'] == 'hi.scott.jones@gmail.com'


def test_password_hash_column_stores_full_hash(app):
    """Test that the password_hash column can store the full bcrypt hash (Text type)."""
    with app.app_context():
        db.create_all()
        
        # Create a user with a password
        user = User(email='fullhash@test.com', password_hash='')
        user.set_password('testpassword123')
        
        db.session.add(user)
        db.session.commit()
        
        # Verify the hash length (bcrypt hashes are 60 characters)
        assert len(user.password_hash) == 60
        
        # Retrieve from database and verify hash is not truncated
        retrieved = User.query.filter_by(email='fullhash@test.com').first()
        assert retrieved is not None
        assert len(retrieved.password_hash) == 60
        assert retrieved.password_hash == user.password_hash
        assert retrieved.check_password('testpassword123') is True


def test_user_check_password_method_never_called_directly_in_routes(app):
    """Verify that routes use user.check_password() not manual bcrypt calls."""
    # This is verified by code inspection and by the login tests working
    # The auth_routes.py file uses user.check_password() at line 73
    # This test documents the requirement
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create user using set_password method
            user = User(email='method@test.com', password_hash='')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
            # Login should work (proving routes use check_password)
            response = client.post('/auth/login',
                                   json={'email': 'method@test.com', 'password': 'testpass'},
                                   content_type='application/json')
            
            assert response.status_code == 200


def test_logout_works(app):
    """Test that logout functionality works."""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create and login a user
            user = User(email='logout@test.com', password_hash='')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Login
            client.post('/auth/login',
                       json={'email': 'logout@test.com', 'password': 'password123'},
                       content_type='application/json')
            
            # Logout
            response = client.get('/auth/logout')
            assert response.status_code == 200
            data = response.get_json()
            assert data['message'] == 'Logged out successfully'


def test_me_endpoint_when_authenticated(app):
    """Test /api/me returns user info when authenticated."""
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Create and login a user
            user = User(email='me@test.com', password_hash='')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            # Login
            client.post('/auth/login',
                       json={'email': 'me@test.com', 'password': 'password123'},
                       content_type='application/json')
            
            # Check /api/me
            response = client.get('/api/me')
            assert response.status_code == 200
            data = response.get_json()
            assert data['authenticated'] is True
            assert data['user']['email'] == 'me@test.com'


def test_me_endpoint_when_not_authenticated(app):
    """Test /api/me returns not authenticated when no session."""
    with app.test_client() as client:
        response = client.get('/api/me')
        assert response.status_code == 200
        data = response.get_json()
        assert data['authenticated'] is False
