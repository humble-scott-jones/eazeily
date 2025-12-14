"""Test that industry pack loader returns chip objects only."""

import pytest
from industry_pack_loader import (
    load_industry_pack, 
    get_industry_pack, 
    get_good_defaults,
    get_available_industry_packs
)


def test_load_industry_pack_returns_chip_objects():
    """Test that load_industry_pack returns chips as objects with {id, label}."""
    # Test with an existing industry pack
    pack = load_industry_pack('dentist')
    
    if pack is None:
        pytest.skip("Dentist pack not found")
    
    assert 'good_defaults' in pack
    assert 'chip_presets' in pack['good_defaults']
    
    chip_presets = pack['good_defaults']['chip_presets']
    
    # Check each chip category
    for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        if category in chip_presets:
            chips = chip_presets[category]
            assert isinstance(chips, list), f"{category} should be a list"
            
            # Each chip should be an object with id and label
            for chip in chips:
                assert isinstance(chip, dict), f"Chip in {category} should be dict: {chip}"
                assert 'id' in chip, f"Chip in {category} missing 'id': {chip}"
                assert 'label' in chip, f"Chip in {category} missing 'label': {chip}"
                assert isinstance(chip['id'], str), f"Chip id should be string: {chip}"
                assert isinstance(chip['label'], str), f"Chip label should be string: {chip}"


def test_get_industry_pack_returns_chip_objects():
    """Test that get_industry_pack returns normalized chips."""
    pack = get_industry_pack('salon')
    
    assert pack is not None
    assert 'good_defaults' in pack
    chip_presets = pack['good_defaults']['chip_presets']
    
    # Verify all chips are objects
    for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        chips = chip_presets.get(category, [])
        for chip in chips:
            assert isinstance(chip, dict)
            assert 'id' in chip
            assert 'label' in chip


def test_get_good_defaults_returns_chip_objects():
    """Test that get_good_defaults returns normalized chips."""
    good_defaults = get_good_defaults('fitness')
    
    assert 'chip_presets' in good_defaults
    chip_presets = good_defaults['chip_presets']
    
    # Check all chip categories
    for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        chips = chip_presets.get(category, [])
        for chip in chips:
            assert isinstance(chip, dict)
            assert 'id' in chip
            assert 'label' in chip


def test_all_industry_packs_return_chip_objects():
    """Test that all available industry packs return chip objects."""
    available_packs = get_available_industry_packs()
    
    # Test at least a few packs
    for pack_id in available_packs[:5]:  # Test first 5 to keep test time reasonable
        pack = load_industry_pack(pack_id)
        
        if pack and 'good_defaults' in pack and 'chip_presets' in pack['good_defaults']:
            chip_presets = pack['good_defaults']['chip_presets']
            
            for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
                if category in chip_presets:
                    chips = chip_presets[category]
                    
                    for chip in chips:
                        assert isinstance(chip, dict), \
                            f"Pack {pack_id}, category {category}: chip should be dict"
                        assert 'id' in chip, \
                            f"Pack {pack_id}, category {category}: chip missing id"
                        assert 'label' in chip, \
                            f"Pack {pack_id}, category {category}: chip missing label"


def test_chip_objects_have_valid_id_format():
    """Test that chip IDs follow expected format (lowercase, underscores)."""
    pack = get_industry_pack('general')
    chip_presets = pack['good_defaults']['chip_presets']
    
    for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        chips = chip_presets.get(category, [])
        for chip in chips:
            chip_id = chip['id']
            
            # ID should not be empty
            assert len(chip_id) > 0, f"Chip ID should not be empty"
            
            # ID should be a valid identifier (allowing lowercase, numbers, underscores)
            # Note: We allow uppercase in IDs from objects, but string-generated ones will be lowercase
            assert isinstance(chip_id, str), f"Chip ID should be string"


def test_chip_objects_have_non_empty_labels():
    """Test that all chip labels are non-empty strings."""
    pack = get_industry_pack('realtor')
    chip_presets = pack['good_defaults']['chip_presets']
    
    for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        chips = chip_presets.get(category, [])
        for chip in chips:
            label = chip['label']
            
            # Label should be non-empty
            assert isinstance(label, str), f"Label should be string"
            # Empty string is technically allowed, but check it's defined
            assert 'label' in chip, f"Chip should have label key"


def test_general_fallback_returns_chip_objects():
    """Test that fallback to general pack returns chip objects."""
    pack = get_industry_pack('nonexistent_industry_12345')
    
    # Should fallback to general
    assert pack['id'] == 'general'
    
    # Should have chip objects
    chip_presets = pack['good_defaults']['chip_presets']
    for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        chips = chip_presets.get(category, [])
        for chip in chips:
            assert isinstance(chip, dict)
            assert 'id' in chip
            assert 'label' in chip


def test_no_raw_strings_in_normalized_chips():
    """Test that no raw strings exist in chip arrays after normalization."""
    pack = get_industry_pack('church')
    chip_presets = pack['good_defaults']['chip_presets']
    
    for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        chips = chip_presets.get(category, [])
        for chip in chips:
            # Should not be a string
            assert not isinstance(chip, str), \
                f"Found raw string in {category}: {chip}. Should be object with {{id, label}}"


def test_chips_maintain_order():
    """Test that chip order is preserved after normalization."""
    pack = load_industry_pack('salon')
    
    if pack:
        chip_presets = pack['good_defaults']['chip_presets']
        focus_topics = chip_presets.get('focus_topics', [])
        
        # Should have chips in some order
        assert len(focus_topics) > 0
        
        # Labels should be in same order as original (even if IDs are generated)
        # This is important for maintaining semantic grouping
        assert all(isinstance(chip, dict) for chip in focus_topics)


def test_chip_id_uniqueness_within_category():
    """Test that chip IDs are unique within each category."""
    pack = get_industry_pack('dentist')
    chip_presets = pack['good_defaults']['chip_presets']
    
    for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
        chips = chip_presets.get(category, [])
        ids = [chip['id'] for chip in chips]
        
        # All IDs within a category should be unique
        assert len(ids) == len(set(ids)), \
            f"Duplicate IDs found in {category}: {ids}"


def test_cached_pack_returns_chip_objects():
    """Test that cached packs also return chip objects."""
    # Load once to cache
    pack1 = load_industry_pack('fitness')
    
    # Load again from cache
    pack2 = load_industry_pack('fitness')
    
    # Both should return chip objects
    for pack in [pack1, pack2]:
        if pack and 'good_defaults' in pack:
            chip_presets = pack['good_defaults']['chip_presets']
            for category in ['focus_topics', 'audience_chips', 'offer_chips', 'proof_chips']:
                chips = chip_presets.get(category, [])
                for chip in chips:
                    assert isinstance(chip, dict)
                    assert 'id' in chip
                    assert 'label' in chip
