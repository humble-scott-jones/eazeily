"""
Tests for the secrets utility module.
"""
import pytest
import os
from unittest.mock import patch, MagicMock
from secrets_util import (
    get_secret,
    get_secret_or_none,
    clear_secret_cache,
    is_production,
    preload_secrets
)


def test_is_production_development():
    """Test production detection in development mode."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development'}):
        assert not is_production()


def test_is_production_production():
    """Test production detection in production mode."""
    with patch.dict(os.environ, {'FLASK_ENV': 'production'}):
        assert is_production()


def test_is_production_with_secret_manager_flag():
    """Test production detection with USE_SECRET_MANAGER flag."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development', 'USE_SECRET_MANAGER': '1'}):
        assert is_production()


def test_get_secret_from_env_fallback():
    """Test getting secret from environment variable fallback."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development', 'TEST_SECRET': 'test_value'}):
        clear_secret_cache()
        result = get_secret('test-secret', fallback_env='TEST_SECRET')
        assert result == 'test_value'


def test_get_secret_not_found():
    """Test that get_secret raises ValueError when secret not found."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development'}, clear=True):
        clear_secret_cache()
        with pytest.raises(ValueError, match="Secret 'nonexistent-secret' not found"):
            get_secret('nonexistent-secret', fallback_env='NONEXISTENT_ENV')


def test_get_secret_or_none_returns_none():
    """Test that get_secret_or_none returns None instead of raising."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development'}, clear=True):
        clear_secret_cache()
        result = get_secret_or_none('nonexistent-secret', fallback_env='NONEXISTENT_ENV')
        assert result is None


def test_get_secret_or_none_returns_value():
    """Test that get_secret_or_none returns value when found."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development', 'TEST_SECRET': 'test_value'}):
        clear_secret_cache()
        result = get_secret_or_none('test-secret', fallback_env='TEST_SECRET')
        assert result == 'test_value'


def test_secret_caching():
    """Test that secrets are cached properly."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development', 'TEST_SECRET': 'cached_value'}):
        clear_secret_cache()
        
        # First call should fetch
        result1 = get_secret('test-secret', fallback_env='TEST_SECRET', cache=True)
        
        # Second call should use cache (change env var to verify)
        os.environ['TEST_SECRET'] = 'new_value'
        result2 = get_secret('test-secret', fallback_env='TEST_SECRET', cache=True)
        
        # Should return cached value
        assert result1 == result2 == 'cached_value'


def test_secret_no_caching():
    """Test that caching can be disabled."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development', 'TEST_SECRET': 'value1'}):
        clear_secret_cache()
        
        # First call
        result1 = get_secret('test-secret', fallback_env='TEST_SECRET', cache=False)
        
        # Change value
        os.environ['TEST_SECRET'] = 'value2'
        result2 = get_secret('test-secret', fallback_env='TEST_SECRET', cache=False)
        
        # Should return new value
        assert result1 == 'value1'
        assert result2 == 'value2'


def test_clear_secret_cache():
    """Test that cache can be cleared."""
    with patch.dict(os.environ, {'FLASK_ENV': 'development', 'TEST_SECRET': 'initial'}):
        clear_secret_cache()
        
        # Cache a value
        get_secret('test-secret', fallback_env='TEST_SECRET', cache=True)
        
        # Change value and clear cache
        os.environ['TEST_SECRET'] = 'updated'
        clear_secret_cache()
        
        # Should fetch new value
        result = get_secret('test-secret', fallback_env='TEST_SECRET', cache=True)
        assert result == 'updated'


def test_preload_secrets():
    """Test preloading multiple secrets."""
    with patch.dict(os.environ, {
        'FLASK_ENV': 'development',
        'SECRET1': 'value1',
        'SECRET2': 'value2'
    }):
        clear_secret_cache()
        
        secret_mapping = {
            'secret-1': 'SECRET1',
            'secret-2': 'SECRET2',
            'secret-3': 'NONEXISTENT'  # This should fail gracefully
        }
        
        results = preload_secrets(secret_mapping)
        
        assert results['secret-1'] is True
        assert results['secret-2'] is True
        assert results['secret-3'] is False


def test_secret_not_logged():
    """Test that secret values are never logged."""
    import logging
    from io import StringIO
    
    # Capture logs
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    
    logger = logging.getLogger('secrets_util')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    with patch.dict(os.environ, {'FLASK_ENV': 'development', 'TEST_SECRET': 'super_secret_value'}):
        clear_secret_cache()
        get_secret('test-secret', fallback_env='TEST_SECRET')
        
        # Check that secret value is not in logs
        log_contents = log_capture.getvalue()
        assert 'super_secret_value' not in log_contents
        
        # But the secret ID should be logged
        assert 'test-secret' in log_contents
    
    logger.removeHandler(handler)
