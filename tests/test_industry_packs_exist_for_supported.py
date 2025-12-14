"""Test that all supported industries have industry packs defined."""

import json
import pytest
from pathlib import Path
from industry_pack_loader import get_available_industry_packs, load_industry_pack, get_industry_pack


def get_supported_industries():
    """Get list of supported industries from config.json."""
    config_path = Path(__file__).parent.parent / "static" / "content" / "config.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    # Extract industry keys from config
    industries = [ind['key'] for ind in config.get('industries', [])]
    return industries


def test_all_supported_industries_have_packs():
    """Test that every industry in config.json has a corresponding industry pack."""
    supported_industries = get_supported_industries()
    available_packs = get_available_industry_packs()
    
    # Add 'general' to available packs since it's a fallback
    if 'general' not in available_packs:
        available_packs.append('general')
    
    missing_packs = []
    for industry in supported_industries:
        # 'other' is expected to fall back to 'general'
        if industry == 'other':
            continue
        
        if industry not in available_packs:
            missing_packs.append(industry)
    
    assert len(missing_packs) == 0, \
        f"Missing industry packs for: {', '.join(missing_packs)}"


def test_general_pack_exists():
    """Test that the 'general' fallback pack exists."""
    available_packs = get_available_industry_packs()
    assert 'general' in available_packs, "General fallback pack must exist"


@pytest.mark.parametrize("industry_key", get_supported_industries())
def test_each_supported_industry_loads_successfully(industry_key):
    """Test that each supported industry can be loaded (directly or via fallback)."""
    # This should never return None due to fallback logic
    pack = get_industry_pack(industry_key)
    assert pack is not None, f"Failed to load pack for {industry_key} (even with fallback)"
    assert 'id' in pack, f"Pack for {industry_key} missing 'id' field"
    assert 'display_name' in pack, f"Pack for {industry_key} missing 'display_name' field"


def test_all_non_other_industries_have_dedicated_packs():
    """Test that all industries except 'other' have their own dedicated packs."""
    supported_industries = get_supported_industries()
    available_packs = get_available_industry_packs()
    
    for industry in supported_industries:
        if industry == 'other':
            # 'other' is allowed to use fallback
            continue
        
        # Try to load directly (not via get_industry_pack which has fallback)
        pack = load_industry_pack(industry)
        assert pack is not None, \
            f"Industry '{industry}' should have a dedicated pack file, not rely on fallback"
        assert pack['id'] == industry, \
            f"Industry pack for '{industry}' has mismatched ID: {pack.get('id')}"


def test_supported_industries_have_required_fields():
    """Test that all supported industry packs have required fields including good_defaults."""
    supported_industries = get_supported_industries()
    
    required_top_level = [
        'id', 'display_name', 'primary_customer_goal', 'version',
        'business_profile_fields', 'default_channel_strategy', 'keyword_banks',
        'cta_library', 'compliance_safety_rules', 'content_templates',
        'example_outputs', 'prompt_integration_hooks', 'good_defaults'
    ]
    
    for industry in supported_industries:
        if industry == 'other':
            continue
            
        pack = load_industry_pack(industry)
        if not pack:
            # Will be caught by other test
            continue
        
        for field in required_top_level:
            assert field in pack, \
                f"Industry '{industry}' missing required field: {field}"


def test_all_packs_have_good_defaults_structure():
    """Test that all industry packs have the complete good_defaults structure."""
    supported_industries = get_supported_industries()
    
    required_good_defaults_fields = [
        'audience', 'offers', 'proof', 'content_angles', 
        'do_say', 'dont_say', 'chip_presets'
    ]
    
    for industry in supported_industries:
        if industry == 'other':
            continue
            
        pack = load_industry_pack(industry)
        if not pack:
            continue
        
        good_defaults = pack.get('good_defaults', {})
        for field in required_good_defaults_fields:
            assert field in good_defaults, \
                f"Industry '{industry}' good_defaults missing: {field}"
        
        # Check chip_presets structure
        chip_presets = good_defaults.get('chip_presets', {})
        required_chip_types = ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']
        for chip_type in required_chip_types:
            assert chip_type in chip_presets, \
                f"Industry '{industry}' chip_presets missing: {chip_type}"
            assert isinstance(chip_presets[chip_type], list), \
                f"Industry '{industry}' chip_presets.{chip_type} should be a list"
            
            # Validate minimum counts per schema
            if chip_type == 'focus_topics':
                assert len(chip_presets[chip_type]) >= 8, \
                    f"Industry '{industry}' chip_presets.{chip_type} should have at least 8 items (schema requires 8-12)"
            else:  # audience_chips, offer_chips, proof_chips
                assert len(chip_presets[chip_type]) >= 6, \
                    f"Industry '{industry}' chip_presets.{chip_type} should have at least 6 items (schema requires 6-10)"
