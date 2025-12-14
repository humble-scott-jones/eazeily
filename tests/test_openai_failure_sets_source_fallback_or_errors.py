"""Test that OpenAI failures properly set source to fallback or return errors."""

import pytest
from unittest.mock import Mock, patch
from generation_service import GenerationService


def test_openai_failure_returns_fallback_with_source():
    """When OpenAI fails and fallback succeeds, response should have source=fallback."""
    service = GenerationService()
    
    # Mock OpenAI to fail
    def failing_openai(payload):
        raise Exception("OpenAI API error")
    
    # Mock fallback to succeed
    def working_fallback(payload):
        return {"posts": [{"date": "2024-01-01", "pillar": "Test", "cards": []}], "count": 1}
    
    # Mock validator to pass through
    def validator(payload):
        return {}
    
    def normalizer(payload):
        return payload
    
    def output_validator(data):
        return data
    
    response = service.generate(
        endpoint='test',
        request_id='test-123',
        payload={'test': 'data'},
        validator=validator,
        normalizer=normalizer,
        output_validator=output_validator,
        openai_callable=failing_openai,
        fallback_callable=working_fallback,
        use_openai=True,
    )
    
    # Should succeed with fallback
    assert response.ok is True
    assert response.body['ok'] is True
    assert response.body['source'] == 'fallback'
    assert response.body['mode'] == 'fallback_suggestions'
    assert 'warnings' in response.body
    assert len(response.body['warnings']) > 0
    assert 'temporarily unavailable' in response.body['warnings'][0].lower()


def test_openai_success_returns_openai_source():
    """When OpenAI succeeds, response should have source=openai."""
    service = GenerationService()
    
    # Mock OpenAI to succeed
    def working_openai(payload):
        return {"posts": [{"date": "2024-01-01", "pillar": "Test", "cards": []}], "count": 1}
    
    # Mock validator to pass through
    def validator(payload):
        return {}
    
    def normalizer(payload):
        return payload
    
    def output_validator(data):
        return data
    
    response = service.generate(
        endpoint='test',
        request_id='test-123',
        payload={'test': 'data'},
        validator=validator,
        normalizer=normalizer,
        output_validator=output_validator,
        openai_callable=working_openai,
        fallback_callable=None,
        use_openai=True,
    )
    
    # Should succeed with OpenAI
    assert response.ok is True
    assert response.body['ok'] is True
    assert response.body['source'] == 'openai'
    assert response.body['mode'] == 'generated'
    assert response.body.get('warnings') is None


def test_openai_failure_no_fallback_returns_error():
    """When OpenAI fails and no fallback, should return error."""
    service = GenerationService()
    
    # Mock OpenAI to fail
    def failing_openai(payload):
        raise Exception("OpenAI API error")
    
    # Mock validator to pass through
    def validator(payload):
        return {}
    
    def normalizer(payload):
        return payload
    
    def output_validator(data):
        return data
    
    response = service.generate(
        endpoint='test',
        request_id='test-123',
        payload={'test': 'data'},
        validator=validator,
        normalizer=normalizer,
        output_validator=output_validator,
        openai_callable=failing_openai,
        fallback_callable=None,
        use_openai=True,
    )
    
    # Should fail
    assert response.ok is False
    assert response.body['ok'] is False
    assert 'error' in response.body
    assert response.body['source'] == 'fallback'
    assert response.body['mode'] == 'error'


def test_no_openai_uses_fallback_with_source():
    """When OpenAI is not available, should use fallback with source=fallback."""
    service = GenerationService()
    
    # Mock fallback to succeed
    def working_fallback(payload):
        return {"posts": [{"date": "2024-01-01", "pillar": "Test", "cards": []}], "count": 1}
    
    # Mock validator to pass through
    def validator(payload):
        return {}
    
    def normalizer(payload):
        return payload
    
    def output_validator(data):
        return data
    
    response = service.generate(
        endpoint='test',
        request_id='test-123',
        payload={'test': 'data'},
        validator=validator,
        normalizer=normalizer,
        output_validator=output_validator,
        openai_callable=None,
        fallback_callable=working_fallback,
        use_openai=False,
    )
    
    # Should succeed with fallback
    assert response.ok is True
    assert response.body['ok'] is True
    assert response.body['source'] == 'fallback'
    assert response.body['mode'] == 'fallback_suggestions'
    assert 'warnings' in response.body


def test_new_generation_service_includes_source():
    """Test that new GenerationService also includes source and mode."""
    from services.generation import GenerationService as NewGenerationService
    
    service = NewGenerationService(enable_openai=False)
    
    result = service.generate_social_posts(
        request={
            'session_length': 1,
            'platforms': ['instagram'],
            'tone': 'friendly'
        }
    )
    
    # Should have source and mode
    assert 'source' in result
    assert 'mode' in result
    assert result['source'] == 'fallback'
    assert result['mode'] == 'fallback_suggestions'
    assert result['ok'] is True
    assert result['openai_used'] is False
    
    # Should have warning
    if result['ok']:
        assert 'warnings' in result
        assert result['warnings'] is not None
        assert len(result['warnings']) > 0
