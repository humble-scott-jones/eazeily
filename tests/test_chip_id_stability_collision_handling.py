"""Test chip ID stability and collision handling."""

import pytest
from industry_pack_loader import generate_chip_id, normalize_chip, normalize_chip_list


def test_chip_id_stability_same_input_same_id():
    """Test that the same label always generates the same ID."""
    label = "Teeth Cleaning Service"
    
    id1 = generate_chip_id(label)
    id2 = generate_chip_id(label)
    id3 = generate_chip_id(label)
    
    assert id1 == id2 == id3


def test_chip_id_stability_across_normalize_calls():
    """Test that normalize_chip generates stable IDs."""
    label = "Preventive Care"
    
    result1 = normalize_chip(label)
    result2 = normalize_chip(label)
    result3 = normalize_chip(label)
    
    assert result1['id'] == result2['id'] == result3['id']


def test_collision_handling_same_label_different_ids():
    """Test that duplicate labels in a list get unique IDs."""
    chips = [
        "Service",
        "Service",
        "Service"
    ]
    result = normalize_chip_list(chips)
    
    ids = [chip['id'] for chip in result]
    
    # All IDs should be unique
    assert len(ids) == len(set(ids))
    
    # First occurrence should get base ID
    assert result[0]['id'] == 'service'
    
    # Subsequent occurrences should get hash suffix
    assert result[1]['id'] != 'service'
    assert result[2]['id'] != 'service'
    assert result[1]['id'] != result[2]['id']


def test_collision_handling_preserves_labels():
    """Test that collision handling preserves original labels."""
    chips = [
        "Same Label",
        "Same Label",
        "Same Label"
    ]
    result = normalize_chip_list(chips)
    
    # All labels should be preserved
    assert result[0]['label'] == "Same Label"
    assert result[1]['label'] == "Same Label"
    assert result[2]['label'] == "Same Label"


def test_collision_hash_suffix_format():
    """Test that collision suffix is a hash."""
    existing_ids = {"service"}
    collision_id = generate_chip_id("Service", existing_ids)
    
    # Should have format: base_id + '_' + hash
    parts = collision_id.split('_')
    assert len(parts) >= 2
    assert parts[0] == 'service'
    # Hash suffix should be 6 characters (as per MD5[:6])
    assert len(parts[-1]) == 6


def test_collision_hash_is_stable():
    """Test that collision hash is deterministic."""
    existing_ids = {"cleaning"}
    
    id1 = generate_chip_id("Cleaning", existing_ids)
    id2 = generate_chip_id("Cleaning", existing_ids)
    
    assert id1 == id2


def test_no_collision_returns_base_id():
    """Test that when there's no collision, base ID is returned."""
    existing_ids = set()
    chip_id = generate_chip_id("Unique Service", existing_ids)
    
    assert chip_id == "unique_service"


def test_collision_with_existing_ids_set():
    """Test collision detection with existing IDs."""
    existing_ids = {"service_a", "service_b", "service_c"}
    
    # This should not collide
    id1 = generate_chip_id("Service D", existing_ids)
    assert id1 == "service_d"
    
    # This should collide
    id2 = generate_chip_id("Service A", existing_ids)
    assert id2 != "service_a"
    assert id2.startswith("service_a_")


def test_normalize_chip_list_builds_collision_set():
    """Test that normalize_chip_list tracks IDs to prevent collisions."""
    chips = [
        "First Service",
        "Second Service",
        "First Service",  # Duplicate
        "Third Service"
    ]
    result = normalize_chip_list(chips)
    
    # Extract IDs
    ids = [chip['id'] for chip in result]
    
    # All should be unique
    assert len(ids) == len(set(ids))
    
    # First and third should have different IDs (collision handled)
    assert result[0]['id'] != result[2]['id']


def test_similar_labels_different_ids():
    """Test that similar but different labels get different base IDs."""
    chips = [
        "Service A",
        "Service B",
        "Service C"
    ]
    result = normalize_chip_list(chips)
    
    # All should have different IDs
    ids = [chip['id'] for chip in result]
    assert len(ids) == len(set(ids))
    
    # Should use slugified versions without collision handling
    assert result[0]['id'] == "service_a"
    assert result[1]['id'] == "service_b"
    assert result[2]['id'] == "service_c"


def test_collision_handling_case_insensitive():
    """Test that collision handling treats IDs as case-insensitive."""
    # Since our slugify converts to lowercase, "Service" and "SERVICE" 
    # should both generate "service" and trigger collision
    chips = [
        "Service",
        "SERVICE"
    ]
    result = normalize_chip_list(chips)
    
    # Both should generate "service" as base, second should get hash
    ids = [chip['id'] for chip in result]
    assert ids[0] == "service"
    assert ids[1] != "service"
    assert ids[1].startswith("service_")


def test_collision_handling_with_whitespace_variations():
    """Test that whitespace variations are treated as same base ID."""
    chips = [
        "Service Name",
        "Service  Name",  # Extra space
        "Service   Name"  # More spaces
    ]
    result = normalize_chip_list(chips)
    
    # All should normalize to same base ID "service_name"
    # So second and third should get collision suffix
    ids = [chip['id'] for chip in result]
    assert ids[0] == "service_name"
    assert ids[1] != "service_name"
    assert ids[2] != "service_name"
    assert ids[1] != ids[2]


def test_long_label_generates_long_id():
    """Test that long labels generate appropriately long IDs."""
    label = "Very Long Service Name With Many Words That Keep Going"
    chip_id = generate_chip_id(label)
    
    # Should slugify the whole thing
    assert 'very' in chip_id
    assert 'long' in chip_id
    assert 'service' in chip_id


def test_unicode_handling():
    """Test that unicode characters are handled in slugification."""
    label = "Service with émojis 😊 and ünicödé"
    result = normalize_chip(label)
    
    # Should have an ID (even if unicode is stripped)
    assert len(result['id']) > 0
    # Label should be preserved
    assert result['label'] == label


def test_collision_id_uniqueness_with_many_duplicates():
    """Test that many duplicates all get unique IDs."""
    chips = ["Service"] * 10
    result = normalize_chip_list(chips)
    
    ids = [chip['id'] for chip in result]
    
    # All 10 should have unique IDs
    assert len(set(ids)) == 10


def test_id_stability_independent_of_list_position():
    """Test that ID generation is stable regardless of position in list."""
    # First list with "Service" at position 0
    chips1 = ["Service", "Other"]
    result1 = normalize_chip_list(chips1)
    
    # Second list with "Other" at position 0
    chips2 = ["Other", "Service"]
    result2 = normalize_chip_list(chips2)
    
    # "Service" should get the same base ID in both cases
    assert result1[0]['id'] == "service"
    assert result2[1]['id'] == "service"
