"""Test that unknown industries fall back to 'general' pack."""

import pytest
from industry_pack_loader import (
    get_industry_pack, 
    load_industry_pack,
    get_good_defaults
)


def test_unknown_industry_returns_general_pack():
    """Test that requesting an unknown industry returns the 'general' pack."""
    # Request a pack that definitely doesn't exist
    pack = get_industry_pack('definitely_not_a_real_industry_12345')
    
    assert pack is not None, "get_industry_pack should never return None"
    assert pack['id'] == 'general', "Unknown industry should return 'general' pack"
    assert pack['display_name'] == 'General Business', "Should return general pack details"


def test_get_industry_pack_never_returns_none():
    """Test that get_industry_pack never returns None even for invalid inputs."""
    invalid_inputs = [
        'nonexistent',
        'fake_industry',
        '',
        'UPPERCASE_INDUSTRY',
        '123numeric',
        'with-dashes',
        'with spaces'
    ]
    
    for invalid_input in invalid_inputs:
        pack = get_industry_pack(invalid_input)
        assert pack is not None, \
            f"get_industry_pack('{invalid_input}') should not return None"
        # Should fallback to general
        assert 'id' in pack, f"Pack should have an id field"


def test_load_vs_get_industry_pack_fallback_behavior():
    """Test the difference between load_industry_pack and get_industry_pack."""
    unknown_industry = 'this_industry_does_not_exist'
    
    # load_industry_pack should return None for unknown
    loaded = load_industry_pack(unknown_industry)
    assert loaded is None, "load_industry_pack should return None for unknown industry"
    
    # get_industry_pack should fallback to general
    gotten = get_industry_pack(unknown_industry)
    assert gotten is not None, "get_industry_pack should use fallback"
    assert gotten['id'] == 'general', "Should fallback to general pack"


def test_general_pack_has_all_required_fields():
    """Test that the general fallback pack has all required fields."""
    general = get_industry_pack('general')
    
    assert general is not None
    assert general['id'] == 'general'
    
    required_fields = [
        'id', 'display_name', 'primary_customer_goal', 'version',
        'business_profile_fields', 'default_channel_strategy', 'keyword_banks',
        'cta_library', 'compliance_safety_rules', 'content_templates',
        'example_outputs', 'prompt_integration_hooks', 'good_defaults'
    ]
    
    for field in required_fields:
        assert field in general, f"General pack missing required field: {field}"


def test_general_pack_has_complete_good_defaults():
    """Test that general pack has complete good_defaults structure."""
    general = get_industry_pack('general')
    good_defaults = general.get('good_defaults', {})
    
    assert 'audience' in good_defaults
    assert 'who' in good_defaults['audience']
    assert 'pain_points' in good_defaults['audience']
    assert 'desired_outcomes' in good_defaults['audience']
    
    assert 'offers' in good_defaults
    assert 'common_services' in good_defaults['offers']
    assert 'ctas' in good_defaults['offers']
    
    assert 'proof' in good_defaults
    assert 'common_proof_points' in good_defaults['proof']
    
    assert 'content_angles' in good_defaults
    assert len(good_defaults['content_angles']) >= 6
    
    assert 'chip_presets' in good_defaults
    chip_presets = good_defaults['chip_presets']
    assert 'focus_topics' in chip_presets
    assert 'audience_chips' in chip_presets
    assert 'offer_chips' in chip_presets
    assert 'proof_chips' in chip_presets


def test_get_good_defaults_for_unknown_industry():
    """Test that get_good_defaults works for unknown industries via fallback."""
    good_defaults = get_good_defaults('unknown_industry_xyz')
    
    assert good_defaults is not None
    assert isinstance(good_defaults, dict)
    # Should have returned general pack's good_defaults
    assert 'chip_presets' in good_defaults


def test_get_good_defaults_returns_dict_for_valid_strings():
    """Test that get_good_defaults returns a dict for string inputs (valid or invalid)."""
    # Test various string inputs (valid and invalid industry names)
    test_cases = ['', 'nonexistent', 'general', 'unknown_xyz', 'salon']
    
    for test_input in test_cases:
        result = get_good_defaults(test_input)
        assert isinstance(result, dict), \
            f"get_good_defaults should return dict for string input '{test_input}'"
        # Should always have chip_presets due to fallback
        assert 'chip_presets' in result or result == {}, \
            f"Result should have chip_presets or be empty dict"


def test_other_industry_uses_fallback():
    """Test that 'other' industry appropriately uses fallback."""
    pack = get_industry_pack('other')
    
    # 'other' might not have its own pack, so it should fallback
    assert pack is not None
    assert 'good_defaults' in pack
    assert 'chip_presets' in pack['good_defaults']


def test_chip_presets_in_general_are_industry_agnostic():
    """Test that general pack's chip presets are appropriately generic."""
    general = get_industry_pack('general')
    chip_presets = general['good_defaults']['chip_presets']
    
    # Check that chips are generic, not industry-specific
    focus_topics = chip_presets['focus_topics']
    
    # Should have generic terms
    generic_terms = ['Quality service', 'Customer satisfaction', 'Professional']
    found_generic = any(any(term.lower() in chip.lower() for term in generic_terms) 
                       for chip in focus_topics)
    
    assert found_generic, "General pack should have generic focus topics"
    
    # Should not have industry-specific terms
    specific_terms = ['haircut', 'dental', 'workout', 'cleaning']
    found_specific = any(any(term.lower() in chip.lower() for term in specific_terms) 
                        for chip in focus_topics)
    
    assert not found_specific, "General pack should not have industry-specific terms"


def test_fallback_maintains_schema_compliance():
    """Test that fallback pack follows the same schema as other packs."""
    from industry_pack_loader import validate_industry_pack
    
    general = get_industry_pack('unknown_will_fallback')
    errors = validate_industry_pack(general)
    
    assert len(errors) == 0, \
        f"General fallback pack should be schema-compliant, but has errors: {errors}"
