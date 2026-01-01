"""
Test database configuration for Railway PostgreSQL deployment.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


def test_postgres_url_converted_to_postgresql():
    """Test that postgres:// URLs are converted to postgresql:// for SQLAlchemy compatibility."""
    with patch.dict(os.environ, {'DATABASE_URL': 'postgres://user:pass@host:5432/db'}):
        # Mock db.create_all to avoid actual database connection
        with patch('app.db.create_all'):
            from app import create_app
            app = create_app()
            
            # Should convert postgres:// to postgresql://
            assert app.config['SQLALCHEMY_DATABASE_URI'] == 'postgresql://user:pass@host:5432/db'


def test_postgresql_url_unchanged():
    """Test that postgresql:// URLs are not modified."""
    with patch.dict(os.environ, {'DATABASE_URL': 'postgresql://user:pass@host:5432/db'}):
        # Mock db.create_all to avoid actual database connection
        with patch('app.db.create_all'):
            from app import create_app
            app = create_app()
            
            # Should remain as postgresql://
            assert app.config['SQLALCHEMY_DATABASE_URI'] == 'postgresql://user:pass@host:5432/db'


def test_no_database_url_uses_sqlite():
    """Test that when DATABASE_URL is not set, SQLite is used."""
    with patch.dict(os.environ, {}, clear=True):
        # Clear DATABASE_URL if it exists
        os.environ.pop('DATABASE_URL', None)
        
        from app import create_app
        app = create_app()
        
        # Should fall back to SQLite
        assert app.config['SQLALCHEMY_DATABASE_URI'] == 'sqlite:///local.db'


def test_tables_created_on_app_initialization():
    """Test that database tables are created when app is initialized."""
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop('DATABASE_URL', None)
        
        from app import create_app
        from models import db, User, VoiceProfile
        
        app = create_app()
        
        # Verify tables exist by checking if we can query them
        with app.app_context():
            # This should not raise an error if tables were created
            try:
                # Query should work if table exists
                User.query.all()
                VoiceProfile.query.all()
                tables_exist = True
            except Exception:
                tables_exist = False
            
            assert tables_exist, "Database tables should be created on app initialization"
