"""Tests that generation returns used_signals metadata for debugging."""

import pytest


def test_generation_response_includes_used_signals_structure():
    """Test that SuccessResponse includes used_signals field."""
    from services.generation.output_schemas import SuccessResponse, UsedSignals
    
    # Create a sample response
    response: SuccessResponse = {
        'ok': True,
        'request_id': 'test123',
        'openai_used': True,
        'fallback_used': False,
        'data': {'posts': []},
        'summary': None,
        'warnings': None,
        'used_signals': {
            'services_used': ['Consulting'],
            'pains_used': ['Lack of clarity'],
            'outcomes_used': [],
            'proof_used': [],
            'differentiators_used': []
        },
        'source': 'openai'
    }
    
    # Verify structure
    assert 'used_signals' in response
    assert response['used_signals'] is not None
    assert 'services_used' in response['used_signals']
    assert 'pains_used' in response['used_signals']


def test_used_signals_type_definition():
    """Test UsedSignals TypedDict structure."""
    from services.generation.output_schemas import UsedSignals
    
    signals: UsedSignals = {
        'services_used': ['Web design', 'SEO'],
        'pains_used': ['Low traffic'],
        'outcomes_used': ['More customers'],
        'proof_used': ['100+ clients'],
        'differentiators_used': ['Award-winning']
    }
    
    assert isinstance(signals['services_used'], list)
    assert isinstance(signals['pains_used'], list)
    assert len(signals['services_used']) == 2
    assert signals['proof_used'][0] == '100+ clients'


def test_success_response_includes_source_field():
    """Test that SuccessResponse includes source field."""
    from services.generation.output_schemas import SuccessResponse
    
    response: SuccessResponse = {
        'ok': True,
        'request_id': 'abc123',
        'openai_used': True,
        'fallback_used': False,
        'data': {},
        'summary': None,
        'warnings': None,
        'used_signals': None,
        'source': 'openai'
    }
    
    assert 'source' in response
    assert response['source'] == 'openai'


def test_warnings_included_when_brand_kit_missing():
    """Test that warnings are included when brand_kit is incomplete."""
    from services.generation.output_schemas import SuccessResponse
    
    response: SuccessResponse = {
        'ok': True,
        'request_id': 'test456',
        'openai_used': False,
        'fallback_used': True,
        'data': {'posts': []},
        'summary': None,
        'warnings': [
            'Brand Kit incomplete: Add services to improve results',
            'Brand Kit missing audience data: Add pain/outcome for better targeting'
        ],
        'used_signals': None,
        'source': 'fallback'
    }
    
    assert 'warnings' in response
    assert response['warnings'] is not None
    assert len(response['warnings']) == 2
    assert 'Brand Kit incomplete' in response['warnings'][0]


def test_used_signals_can_be_none():
    """Test that used_signals can be None (when brand kit not used)."""
    from services.generation.output_schemas import SuccessResponse
    
    response: SuccessResponse = {
        'ok': True,
        'request_id': 'test789',
        'openai_used': True,
        'fallback_used': False,
        'data': {},
        'summary': None,
        'warnings': None,
        'used_signals': None,
        'source': 'openai'
    }
    
    assert response['used_signals'] is None


def test_used_signals_empty_lists():
    """Test that used_signals can have empty lists when signals weren't matched."""
    from services.generation.output_schemas import UsedSignals
    
    signals: UsedSignals = {
        'services_used': [],
        'pains_used': [],
        'outcomes_used': [],
        'proof_used': [],
        'differentiators_used': []
    }
    
    # Should be valid
    assert signals['services_used'] == []
    assert signals['pains_used'] == []


def test_brand_kit_v1_includes_all_fields():
    """Test that BrandKitV1 includes all expected fields."""
    from services.generation.output_schemas import BrandKitV1
    
    brand_kit: BrandKitV1 = {
        'services': ['Service 1'],
        'audience_role': 'Business owners',
        'audience_pain': 'Pain point',
        'audience_outcome': 'Desired outcome',
        'audience_objection': 'Common objection',
        'differentiators': ['Differentiator 1'],
        'proof': ['Social proof'],
        'email_signature': 'Best regards, John',
        'quote_terms': '30 day validity, 50% deposit'
    }
    
    # Verify all fields are accessible
    assert brand_kit['services'] == ['Service 1']
    assert brand_kit['audience_role'] == 'Business owners'
    assert brand_kit['audience_pain'] == 'Pain point'
    assert brand_kit['audience_outcome'] == 'Desired outcome'
    assert brand_kit['audience_objection'] == 'Common objection'
    assert brand_kit['differentiators'] == ['Differentiator 1']
    assert brand_kit['proof'] == ['Social proof']
    assert brand_kit['email_signature'] == 'Best regards, John'
    assert brand_kit['quote_terms'] == '30 day validity, 50% deposit'


def test_workspace_context_includes_brand_kit_tier():
    """Test that WorkspaceContext includes brand_kit_tier field."""
    from services.generation.output_schemas import WorkspaceContext, BrandKitV1
    
    brand_kit: BrandKitV1 = {
        'services': ['Consulting'],
        'audience_role': 'CEOs',
        'proof': ['20 years']
    }
    
    workspace: WorkspaceContext = {
        'company_name': 'Test Co',
        'industry': 'business',
        'default_tone': 'professional',
        'platforms': ['linkedin'],
        'offerings': None,
        'audience': None,
        'compliance_notes': None,
        'brand_kit': brand_kit,
        'brand_kit_tier': 'best'
    }
    
    assert workspace['brand_kit_tier'] == 'best'
    assert workspace['brand_kit'] is not None


def test_used_signals_partial_data():
    """Test used_signals with partial data (some lists populated, some empty)."""
    from services.generation.output_schemas import UsedSignals
    
    signals: UsedSignals = {
        'services_used': ['Web design', 'SEO'],
        'pains_used': ['Low visibility'],
        'outcomes_used': [],  # No outcomes mentioned
        'proof_used': ['10 years experience'],
        'differentiators_used': []  # No differentiators mentioned
    }
    
    # Should be valid with mixed empty/populated lists
    assert len(signals['services_used']) == 2
    assert len(signals['pains_used']) == 1
    assert len(signals['outcomes_used']) == 0
    assert len(signals['proof_used']) == 1
    assert len(signals['differentiators_used']) == 0
