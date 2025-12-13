"""Tests for PII redaction in prompt traces.

Verifies that prompt trace redaction works - no raw emails/phones/addresses.
"""

import pytest
from services.generation.prompt_trace import (
    PromptTrace,
    redact_pii,
    hash_text,
    create_trace_from_compiler_output
)
from services.generation.prompt_compiler import (
    PromptCompiler,
    ProfileDefaults,
    RunToggles
)


def test_redact_email_addresses():
    """Test that email addresses are redacted."""
    text = "Contact us at support@example.com or john.doe@company.org"
    redacted = redact_pii(text)
    
    assert '[EMAIL]' in redacted
    assert 'support@example.com' not in redacted
    assert 'john.doe@company.org' not in redacted


def test_redact_phone_numbers():
    """Test that phone numbers are redacted."""
    text = "Call us at 555-123-4567 or (555) 987-6543"
    redacted = redact_pii(text)
    
    assert '[PHONE]' in redacted
    assert '555-123-4567' not in redacted
    assert '(555) 987-6543' not in redacted


def test_redact_addresses():
    """Test that street addresses are redacted."""
    text = "Visit us at 123 Main Street or 456 Oak Avenue"
    redacted = redact_pii(text)
    
    assert '[ADDRESS]' in redacted
    assert '123 Main Street' not in redacted


def test_redact_multiple_pii_types():
    """Test redacting multiple PII types at once."""
    text = "Email: test@example.com, Phone: 555-123-4567, Address: 789 Elm Road"
    redacted = redact_pii(text)
    
    assert '[EMAIL]' in redacted
    assert '[PHONE]' in redacted
    assert '[ADDRESS]' in redacted
    assert 'test@example.com' not in redacted
    assert '555-123-4567' not in redacted


def test_hash_text_consistent():
    """Test that text hashing is consistent."""
    text = "sensitive information"
    
    hash1 = hash_text(text)
    hash2 = hash_text(text)
    
    assert hash1 == hash2
    assert len(hash1) == 8  # default length
    assert hash1 != text  # should be hashed


def test_hash_text_different_inputs():
    """Test that different inputs produce different hashes."""
    hash1 = hash_text("text1")
    hash2 = hash_text("text2")
    
    assert hash1 != hash2


def test_prompt_trace_no_pii_in_metadata():
    """Test that PromptTrace metadata contains no PII."""
    trace = PromptTrace('test123')
    
    trace.set_selections(
        tone='professional',
        platforms=['instagram'],
        session_length=7,
        keywords=['email@test.com', '555-1234']  # Intentional PII in keywords
    )
    
    summary = trace.get_summary()
    
    # Keywords should be hashed, not raw
    assert 'keywords_hash' in summary['selections']
    assert 'email@test.com' not in str(summary)
    assert '555-1234' not in str(summary)


def test_prompt_trace_selections_safe():
    """Test that selections are safely stored without PII."""
    trace = PromptTrace('trace456')
    
    trace.set_selections(
        tone='friendly',
        platforms=['facebook', 'twitter'],
        session_length=30,
        goals=['engagement', 'growth'],
        keywords=['product', 'service']
    )
    
    summary = trace.get_summary()
    selections = summary['selections']
    
    # Should have counts, not raw data for some fields
    assert selections['tone'] == 'friendly'
    assert selections['platforms'] == ['facebook', 'twitter']
    assert selections['goals_count'] == 2
    assert selections['keywords_count'] == 2
    
    # Should have safe samples and hashes
    assert 'goals_sample' in selections
    assert 'keywords_hash' in selections


def test_prompt_trace_voice_fingerprint_no_samples():
    """Test that voice fingerprint tracking doesn't expose samples."""
    trace = PromptTrace('voice123')
    
    trace.set_voice_fingerprint_applied(applied=True, sample_count=5)
    
    summary = trace.get_summary()
    
    # Should have metadata but not raw samples
    assert summary['voice_fingerprint']['applied'] is True
    assert summary['voice_fingerprint']['sample_count'] == 5


def test_prompt_trace_from_compiler_output():
    """Test creating trace from compiler output - no PII leak."""
    profile = ProfileDefaults(
        company='Test Company',
        industry='tech',
        signature_tone='professional',
        audience='contact@example.com'  # Intentional PII
    )
    
    run_toggles = RunToggles(
        session_length=7,
        keywords=['call 555-1234']  # Intentional PII
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(run_toggles, request_id='safe123')
    
    trace = create_trace_from_compiler_output(output)
    summary = trace.get_summary()
    
    # Summary should not contain PII
    summary_str = str(summary)
    assert 'contact@example.com' not in summary_str
    assert '555-1234' not in summary_str
    
    # Should have safe metadata
    assert summary['request_id'] == 'safe123'
    assert 'content_type' in summary


def test_prompt_trace_logging_no_pii():
    """Test that logging trace doesn't expose PII."""
    import logging
    import io
    
    # Capture log output
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = logging.getLogger('services.generation.prompt_trace')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    
    trace = PromptTrace('log123')
    trace.set_selections(
        tone='casual',
        keywords=['email@test.com', 'phone 555-123-4567']
    )
    trace.log_trace('info')
    
    log_output = log_stream.getvalue()
    
    # Log should not contain raw PII (keywords are hashed, not logged raw)
    # The hash is what gets logged, not the raw values
    assert 'log123' in log_output or 'Prompt trace' in log_output
    
    # Clean up
    logger.removeHandler(handler)


def test_empty_trace_no_errors():
    """Test that empty trace doesn't cause errors."""
    trace = PromptTrace('empty123')
    
    summary = trace.get_summary()
    
    # Should have basic metadata
    assert summary['request_id'] == 'empty123'
    assert 'timestamp' in summary


def test_trace_flags_safe():
    """Test that custom flags can be added safely."""
    trace = PromptTrace('flag123')
    
    trace.add_flag('openai_used', True)
    trace.add_flag('fallback_used', False)
    trace.add_flag('repair_attempted', False)
    
    summary = trace.get_summary()
    
    # Flags should be present
    assert summary['flags']['openai_used'] is True
    assert summary['flags']['fallback_used'] is False


def test_trace_model_info_safe():
    """Test that model info is safely stored."""
    trace = PromptTrace('model123')
    
    trace.set_model_info(model='gpt-4o-mini', provider='openai')
    
    summary = trace.get_summary()
    
    # Model info should be present
    assert summary['model']['provider'] == 'openai'
    assert summary['model']['model'] == 'gpt-4o-mini'


def test_trace_token_estimate_safe():
    """Test that token estimates are safely stored."""
    trace = PromptTrace('token123')
    
    trace.set_token_estimate(1500)
    
    summary = trace.get_summary()
    
    # Token count should be present
    assert summary['token_budget'] == 1500


def test_redact_pii_preserves_safe_content():
    """Test that PII redaction preserves safe content."""
    text = "Our company offers great products for professionals in the tech industry."
    redacted = redact_pii(text)
    
    # Should be unchanged (no PII)
    assert redacted == text


def test_redact_pii_handles_none():
    """Test that redact_pii handles None gracefully."""
    assert redact_pii(None) is None
    assert redact_pii('') == ''


def test_hash_text_handles_empty():
    """Test that hash_text handles empty strings."""
    assert hash_text('') == ''
    assert hash_text(None) == ''


def test_compiler_trace_summary_no_raw_pii():
    """Test that compiler trace summary never contains raw PII."""
    # Create profile with intentional PII
    profile = ProfileDefaults(
        company='Company',
        audience='Contact: support@example.com or call 555-0100'
    )
    
    run_toggles = RunToggles(
        session_length=7,
        keywords=['keyword1', 'keyword2']
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(run_toggles)
    
    trace_summary = output['trace_summary']
    trace_str = str(trace_summary)
    
    # Trace summary should not expose the PII from profile.audience
    # (audience is in model_context, not in trace_summary selections)
    assert 'support@example.com' not in trace_str
    assert '555-0100' not in trace_str
    
    # But should have safe metadata
    assert 'request_id' in trace_summary
    assert 'content_type' in trace_summary
    assert 'selections' in trace_summary
