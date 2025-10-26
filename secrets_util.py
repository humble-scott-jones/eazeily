"""
Secret Management Utility Module

This module provides functions to securely fetch secrets from Google Cloud Secret Manager
in production, while falling back to environment variables in development.

Usage:
    from secrets_util import get_secret
    
    stripe_key = get_secret('stripe-secret-key', fallback_env='STRIPE_SECRET_KEY')
"""

import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache for secrets to reduce API calls
_secret_cache = {}


def is_production():
    """Check if running in production environment."""
    return os.getenv('FLASK_ENV') == 'production' or os.getenv('USE_SECRET_MANAGER') == '1'


def get_secret(secret_id: str, project_id: Optional[str] = None, 
               version: str = "latest", fallback_env: Optional[str] = None,
               cache: bool = True) -> str:
    """
    Fetch a secret from Google Cloud Secret Manager or environment variables.
    
    In production (FLASK_ENV=production or USE_SECRET_MANAGER=1):
        Fetches from Google Cloud Secret Manager
    
    In development:
        Falls back to environment variables
    
    Args:
        secret_id: The ID of the secret in Secret Manager
        project_id: GCP project ID (defaults to GCP_PROJECT_ID env var)
        version: Secret version to fetch (default: "latest")
        fallback_env: Environment variable name to use as fallback in dev
        cache: Whether to cache the secret value (default: True)
    
    Returns:
        The secret value as a string
    
    Raises:
        ValueError: If secret cannot be fetched and no fallback is available
    
    Example:
        >>> stripe_key = get_secret('stripe-secret-key', fallback_env='STRIPE_SECRET_KEY')
    """
    # Check cache first
    cache_key = f"{secret_id}:{version}"
    if cache and cache_key in _secret_cache:
        return _secret_cache[cache_key]
    
    # Log access attempt (but never log the actual secret value)
    logger.info(f"Accessing secret: {secret_id}", extra={
        "secret_id": secret_id,
        "version": version,
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv('FLASK_ENV', 'unknown')
    })
    
    # In production, use Secret Manager
    if is_production():
        try:
            from google.cloud import secretmanager
            
            if project_id is None:
                project_id = os.getenv('GCP_PROJECT_ID')
                if not project_id:
                    raise ValueError("GCP_PROJECT_ID environment variable not set")
            
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
            
            response = client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode('UTF-8')
            
            # Cache the value
            if cache:
                _secret_cache[cache_key] = secret_value
            
            logger.info(f"Successfully fetched secret from Secret Manager: {secret_id}")
            return secret_value
            
        except ImportError:
            logger.warning(
                "google-cloud-secret-manager not installed. "
                "Install with: pip install google-cloud-secret-manager"
            )
            # Fall through to environment variable fallback
        except Exception as e:
            logger.error(
                f"Failed to fetch secret from Secret Manager: {secret_id}",
                extra={"error_type": type(e).__name__, "secret_id": secret_id}
            )
            # Fall through to environment variable fallback
    
    # Fall back to environment variable
    if fallback_env:
        env_value = os.getenv(fallback_env)
        if env_value:
            logger.info(f"Using environment variable fallback: {fallback_env}")
            return env_value
    
    # No secret found
    error_msg = f"Secret '{secret_id}' not found"
    if fallback_env:
        error_msg += f" and fallback environment variable '{fallback_env}' not set"
    
    logger.error(error_msg)
    raise ValueError(error_msg)


def get_secret_or_none(secret_id: str, project_id: Optional[str] = None,
                       version: str = "latest", fallback_env: Optional[str] = None,
                       cache: bool = True) -> Optional[str]:
    """
    Same as get_secret() but returns None instead of raising an exception.
    
    Useful for optional secrets.
    
    Args:
        secret_id: The ID of the secret in Secret Manager
        project_id: GCP project ID (defaults to GCP_PROJECT_ID env var)
        version: Secret version to fetch (default: "latest")
        fallback_env: Environment variable name to use as fallback in dev
        cache: Whether to cache the secret value (default: True)
    
    Returns:
        The secret value as a string, or None if not found
    
    Example:
        >>> openai_key = get_secret_or_none('openai-api-key', fallback_env='OPENAI_API_KEY')
        >>> if openai_key:
        >>>     # Use OpenAI features
    """
    try:
        return get_secret(secret_id, project_id, version, fallback_env, cache)
    except (ValueError, Exception) as e:
        logger.debug(f"Secret not found: {secret_id} ({type(e).__name__})")
        return None


def clear_secret_cache():
    """Clear the secret cache. Useful for testing or after rotating secrets."""
    global _secret_cache
    _secret_cache = {}
    logger.info("Secret cache cleared")


def preload_secrets(secret_mapping: dict, project_id: Optional[str] = None):
    """
    Preload multiple secrets at application startup to reduce latency.
    
    Args:
        secret_mapping: Dict mapping secret IDs to environment variable fallbacks
            Example: {'stripe-secret-key': 'STRIPE_SECRET_KEY'}
        project_id: GCP project ID (defaults to GCP_PROJECT_ID env var)
    
    Returns:
        Dict of successfully loaded secrets (secret_id -> True/False)
    
    Example:
        >>> preload_secrets({
        >>>     'stripe-secret-key': 'STRIPE_SECRET_KEY',
        >>>     'flask-secret-key': 'SECRET_KEY',
        >>> })
    """
    results = {}
    for secret_id, fallback_env in secret_mapping.items():
        try:
            get_secret(secret_id, project_id=project_id, fallback_env=fallback_env, cache=True)
            results[secret_id] = True
        except Exception as e:
            logger.warning(f"Failed to preload secret {secret_id}: {type(e).__name__}")
            results[secret_id] = False
    
    logger.info(f"Preloaded {sum(results.values())}/{len(results)} secrets")
    return results


# Example usage in app.py:
"""
from secrets_util import get_secret, preload_secrets

# Preload secrets at startup (optional but recommended)
preload_secrets({
    'flask-secret-key': 'SECRET_KEY',
    'stripe-secret-key': 'STRIPE_SECRET_KEY',
    'stripe-publishable-key': 'STRIPE_PUBLISHABLE_KEY',
    'stripe-webhook-secret': 'STRIPE_WEBHOOK_SECRET',
    'openai-api-key': 'OPENAI_API_KEY',
})

# Use secrets in your application
app.secret_key = get_secret('flask-secret-key', fallback_env='SECRET_KEY')

# Optional secrets
OPENAI_KEY = get_secret_or_none('openai-api-key', fallback_env='OPENAI_API_KEY')
USE_OPENAI = bool(OPENAI_KEY)
"""
