"""Unit tests for context_builder module."""

import pytest
from services.generation.context_builder import (
    merge_contexts,
    validate_required_fields,
    extract_merged_params,
    get_workspace_summary
)


def test_merge_contexts_precedence():
    """Test that merge follows correct precedence: request > template > profile > workspace."""
    workspace = {
        'company_name': 'Acme Corp',
        'industry': 'software',
        'default_tone': 'professional',
        'platforms': ['linkedin']
    }
    
    profile = {
        'tone': 'friendly',
        'platforms': ['instagram', 'facebook']
    }
    
    template = {
        'tone': 'playful',
        'platforms': ['tiktok']
    }
    
    request = {
        'tone': 'inspiring',
        'session_length': 7
    }
    
    context = merge_contexts(
        workspace=workspace,
        profile=profile,
        template=template,
        request=request
    )
    
    # Request should override template
    merged = context['request']
    assert merged['tone'] == 'inspiring'
    
    # Template platforms should be in merged (not overridden by request)
    assert merged['platforms'] == ['tiktok']
    
    # Session length from request
    assert merged['session_length'] == 7
    
    # Workspace context should be preserved
    workspace_ctx = context['workspace']
    assert workspace_ctx['company_name'] == 'Acme Corp'
    assert workspace_ctx['industry'] == 'software'


def test_merge_contexts_minimal():
    """Test merge with minimal inputs."""
    context = merge_contexts(request={'tone': 'casual'})
    
    assert context is not None
    assert 'workspace' in context
    assert 'request' in context
    assert context['request']['tone'] == 'casual'


def test_merge_contexts_with_voice_guide():
    """Test merge includes voice guide when provided."""
    voice_guide = {
        'tone_descriptors': ['enthusiastic', 'direct'],
        'sentence_length': 'short'
    }
    
    context = merge_contexts(
        request={'tone': 'friendly'},
        voice_guide=voice_guide
    )
    
    assert context['voice_guide'] is not None
    assert context['voice_guide']['tone_descriptors'] == ['enthusiastic', 'direct']


def test_validate_required_fields_success():
    """Test validation passes with all required fields."""
    context = merge_contexts(
        workspace={'industry': 'retail', 'company_name': 'Shop Co'},
        request={'tone': 'friendly'}
    )
    
    errors = validate_required_fields(context, ['industry', 'tone'])
    
    assert len(errors) == 0


def test_validate_required_fields_missing():
    """Test validation fails with missing fields."""
    context = merge_contexts(request={'tone': 'friendly'})
    
    errors = validate_required_fields(context, ['industry', 'company_name'])
    
    # Should have errors for missing fields
    assert len(errors) > 0
    assert 'industry' in errors or 'company_name' in errors


def test_extract_merged_params():
    """Test extraction of flat parameter dict from context."""
    workspace = {
        'company_name': 'Test Co',
        'industry': 'tech',
        'default_tone': 'professional',
        'platforms': ['linkedin']
    }
    
    request = {
        'tone': 'friendly',
        'session_length': 30,
        'platforms': ['instagram', 'facebook'],
        'goals': ['engagement', 'awareness'],
        'keywords': ['innovation', 'tech']
    }
    
    context = merge_contexts(workspace=workspace, request=request)
    params = extract_merged_params(context)
    
    # Check request values override workspace
    assert params['tone'] == 'friendly'
    assert params['platforms'] == ['instagram', 'facebook']
    assert params['session_length'] == 30
    
    # Check workspace values
    assert params['company_name'] == 'Test Co'
    assert params['industry'] == 'tech'
    
    # Check request-specific values
    assert params['goals'] == ['engagement', 'awareness']
    assert params['keywords'] == ['innovation', 'tech']


def test_extract_merged_params_defaults():
    """Test default values in extracted params."""
    context = merge_contexts()
    params = extract_merged_params(context)
    
    # Should have default values
    assert params['tone'] == 'professional'
    assert params['session_length'] == 7
    assert isinstance(params['platforms'], list)
    assert params['industry'] == 'business'


def test_get_workspace_summary():
    """Test generation of workspace summary text."""
    workspace = {
        'company_name': 'Awesome LLC',
        'industry': 'fitness',
        'offerings': 'Personal training and nutrition coaching',
        'audience': 'Health-conscious adults 25-45'
    }
    
    context = merge_contexts(workspace=workspace)
    summary = get_workspace_summary(context)
    
    assert 'Awesome LLC' in summary
    assert 'fitness' in summary
    assert 'Personal training' in summary
    assert 'Health-conscious' in summary


def test_get_workspace_summary_empty():
    """Test workspace summary with no data."""
    context = merge_contexts()
    summary = get_workspace_summary(context)
    
    # Should return empty string or minimal text
    assert isinstance(summary, str)


def test_template_overrides_profile():
    """Test that template values override profile but not request."""
    profile = {
        'tone': 'professional',
        'platforms': ['linkedin'],
        'creativity': 0.7
    }
    
    template = {
        'tone': 'casual',
        'platforms': ['instagram', 'facebook'],
        'goals': ['engagement']
    }
    
    request = {
        'platforms': ['twitter']
    }
    
    context = merge_contexts(
        profile=profile,
        template=template,
        request=request
    )
    
    merged = context['request']
    
    # Request platforms override template
    assert merged['platforms'] == ['twitter']
    
    # Template tone overrides profile (no request override)
    assert merged['tone'] == 'casual'
    
    # Template goals added
    assert merged['goals'] == ['engagement']
    
    # Profile creativity preserved (not in template or request)
    assert merged['creativity'] == 0.7


def test_reel_options_in_request():
    """Test that reel-specific options are preserved."""
    request = {
        'tone': 'energetic',
        'reel_options': {
            'hook_style': 'question',
            'duration': 45,
            'include_shot_list': True
        }
    }
    
    context = merge_contexts(request=request)
    merged = context['request']
    
    assert 'reel_options' in merged
    assert merged['reel_options']['hook_style'] == 'question'
    assert merged['reel_options']['duration'] == 45


def test_use_brand_voice_flag():
    """Test that use_brand_voice flag is preserved."""
    request = {
        'use_brand_voice': True,
        'tone': 'professional'
    }
    
    context = merge_contexts(request=request)
    merged = context['request']
    
    assert merged['use_brand_voice'] is True
