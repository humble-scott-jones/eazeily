"""
Tests for User password methods (set_password and check_password).
"""
import pytest
from models import User, db, bcrypt


def test_set_password_hashes_correctly(app):
    """Test that set_password properly hashes the password."""
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        user = User(email='test@example.com', password_hash='')
        user.set_password('mypassword123')
        
        # The password_hash should be set
        assert user.password_hash != ''
        assert user.password_hash != 'mypassword123'  # Should be hashed, not plain
        # Should start with bcrypt prefix
        assert user.password_hash.startswith('$2b$') or user.password_hash.startswith('$2a$')


def test_check_password_validates_correctly(app):
    """Test that check_password correctly validates passwords."""
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        user = User(email='test@example.com', password_hash='')
        user.set_password('correctpassword')
        
        # Correct password should return True
        assert user.check_password('correctpassword') is True
        
        # Wrong password should return False
        assert user.check_password('wrongpassword') is False
        assert user.check_password('') is False


def test_password_methods_integration(app):
    """Test the full flow: create user, set password, verify password."""
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        # Create a user with set_password
        user = User(email='integration@example.com', password_hash='')
        user.set_password('test1234')
        
        db.session.add(user)
        db.session.commit()
        
        # Query the user back from DB
        retrieved_user = User.query.filter_by(email='integration@example.com').first()
        
        assert retrieved_user is not None
        assert retrieved_user.check_password('test1234') is True
        assert retrieved_user.check_password('wrong') is False


def test_password_change(app):
    """Test that password can be changed."""
    with app.app_context():
        # Ensure tables exist
        db.create_all()
        
        user = User(email='change@example.com', password_hash='')
        user.set_password('oldpassword')
        
        db.session.add(user)
        db.session.commit()
        
        # Verify old password works
        assert user.check_password('oldpassword') is True
        
        # Change password
        user.set_password('newpassword')
        db.session.commit()
        
        # Old password should not work
        assert user.check_password('oldpassword') is False
        
        # New password should work
        assert user.check_password('newpassword') is True

