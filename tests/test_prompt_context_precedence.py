"""Tests for prompt context precedence with chip selections.

Verifies that chips are merged with correct precedence:
request > saved selections (profile) > industry good_defaults > general fallback
"""

import pytest
from services.generation.context_builder import (
    merge_contexts,
    extract_chip_selections,
    extract_brand_kit_from_user_data
)


def test_chip_precedence_request_overrides_profile():
    """Test that request chips override profile saved selections."""
    workspace = {
        'company_name': 'Test Salon',
        'industry': 'salon'
    }
    
    profile = {
        'selected_audience_ids': ['regular_maintenance_clients'],
        'selected_offer_ids': ['new_client_discount'],
        'selected_proof_ids': ['5_star_rated']
    }
    
    request = {
        'selected_audience_ids': ['first_time_clients'],  # Override profile
        'selected_offer_ids': ['free_consultation'],  # Override profile
        # selected_proof_ids not in request, should use profile value
    }
    
    context = merge_contexts(
        workspace=workspace,
        profile=profile,
        request=request
    )
    
    merged = context['request']
    
    # Request overrides profile for audience and offers
    assert merged['selected_audience_ids'] == ['first_time_clients']
    assert merged['selected_offer_ids'] == ['free_consultation']
    
    # Profile value used when not in request
    assert merged['selected_proof_ids'] == ['5_star_rated']


def test_chip_precedence_profile_overrides_industry_defaults():
    """Test that saved profile selections override industry defaults."""
    workspace = {
        'company_name': 'Test Salon',
        'industry': 'salon'
    }
    
    profile = {
        'selected_audience_ids': ['brides_and_bridal_parties'],
        'selected_offer_ids': ['bridal_packages']
    }
    
    request = {
        'tone': 'friendly'
    }
    
    context = merge_contexts(
        workspace=workspace,
        profile=profile,
        request=request
    )
    
    merged = context['request']
    
    # Profile selections should be present
    assert 'selected_audience_ids' in merged
    assert merged['selected_audience_ids'] == ['brides_and_bridal_parties']


def test_chip_extraction_from_brand_kit():
    """Test extraction of chips from Brand Kit data."""
    brand_kit = {
        'services': ['Haircuts', 'Color services', 'Hair treatments'],
        'audience_role': 'Women seeking professional hair services',
        'audience_pain': 'Finding a stylist they can trust',
        'audience_outcome': 'Healthy, beautiful hair',
        'proof': ['10+ years experience', '5-star rated', 'Certified colorists']
    }
    
    chips = extract_chip_selections(brand_kit=brand_kit)
    
    # Services should be extracted as offer chips
    assert 'offers' in chips
    assert len(chips['offers']) == 3
    assert 'Haircuts' in chips['offers']
    
    # Proof should be extracted
    assert 'proof' in chips
    assert len(chips['proof']) == 3


def test_custom_chips_merged_with_standard():
    """Test that custom chips are merged with standard chip selections."""
    profile = {
        'selected_offer_ids': ['consultation'],
        'custom_chips': {
            'offers': [
                {'id': 'custom_package', 'label': 'VIP Hair Transformation Package'}
            ]
        }
    }
    
    request = {
        'tone': 'professional'
    }
    
    context = merge_contexts(
        profile=profile,
        request=request
    )
    
    merged = context['request']
    
    # Both standard and custom chips should be available
    assert 'selected_offer_ids' in merged
    assert 'custom_chips' in merged
    assert merged['custom_chips']['offers'][0]['label'] == 'VIP Hair Transformation Package'


def test_empty_chip_selections_use_industry_defaults():
    """Test that when no chips are selected, industry defaults are available."""
    workspace = {
        'company_name': 'Test Salon',
        'industry': 'salon'
    }
    
    # No profile or request chip selections
    context = merge_contexts(workspace=workspace)
    
    # Context should have workspace industry info for loading defaults
    assert context['workspace']['industry'] == 'salon'


def test_extract_chip_selections_handles_empty_inputs():
    """Test that extract_chip_selections handles empty/None inputs gracefully."""
    chips = extract_chip_selections()
    
    # Should return empty structure
    assert isinstance(chips, dict)
    assert 'audience' in chips
    assert 'offers' in chips
    assert 'proof' in chips
    assert len(chips['audience']) == 0


def test_extract_chip_selections_from_profile():
    """Test extracting chip IDs from profile data."""
    profile = {
        'selected_audience_ids': ['first_time_clients', 'busy_professionals'],
        'selected_offer_ids': ['new_client_discount', 'online_booking'],
        'selected_proof_ids': ['5_star_rated', '10_years_experience']
    }
    
    chips = extract_chip_selections(profile=profile)
    
    assert len(chips['audience']) == 2
    assert 'first_time_clients' in chips['audience']
    assert len(chips['offers']) == 2
    assert 'new_client_discount' in chips['offers']
    assert len(chips['proof']) == 2
    assert '5_star_rated' in chips['proof']
