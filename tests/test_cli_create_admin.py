"""Test the create-admin CLI command."""
import os
from pathlib import Path
from click.testing import CliRunner


def test_create_admin_command():
    """Test the create-admin CLI command creates a user successfully."""
    # Clean up any existing database
    instance_dir = Path('instance')
    if instance_dir.exists():
        for db_file in instance_dir.glob('*.db'):
            db_file.unlink()
    
    from app import create_admin, app
    from models import User
    
    runner = CliRunner()
    result = runner.invoke(create_admin, ['admin@test.com', 'password123'])
    
    assert result.exit_code == 0
    assert 'Successfully created admin: admin@test.com' in result.output
    
    # Verify user was created in the database
    with app.app_context():
        user = User.query.filter_by(email='admin@test.com').first()
        assert user is not None
        assert user.email == 'admin@test.com'
        assert user.password_hash is not None
        assert len(user.password_hash) > 0


def test_create_admin_duplicate():
    """Test that create-admin handles duplicate users correctly."""
    from app import create_admin, app
    
    runner = CliRunner()
    
    # Create user first time (might already exist from previous test)
    result1 = runner.invoke(create_admin, ['duplicate@test.com', 'password123'])
    # Should either succeed or say it exists
    assert result1.exit_code == 0
    assert ('Successfully created admin: duplicate@test.com' in result1.output or 
            'User duplicate@test.com already exists' in result1.output)
    
    # Try to create same user again - should say it exists
    result2 = runner.invoke(create_admin, ['duplicate@test.com', 'password123'])
    assert result2.exit_code == 0
    assert 'User duplicate@test.com already exists' in result2.output


def test_create_admin_password_hashed():
    """Test that the password is properly hashed."""
    from app import create_admin, app
    from models import User, bcrypt
    
    runner = CliRunner()
    email = 'hashtest@test.com'
    password = 'mySecurePassword123'
    
    result = runner.invoke(create_admin, [email, password])
    assert result.exit_code == 0
    
    # Verify password is hashed and can be verified
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        assert user is not None
        # Password should be hashed (not plain text)
        assert user.password_hash != password
        # Should be able to verify the password
        assert bcrypt.check_password_hash(user.password_hash, password)
        # Wrong password should not verify
        assert not bcrypt.check_password_hash(user.password_hash, 'wrongpassword')





