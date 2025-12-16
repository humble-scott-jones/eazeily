"""Test that chip normalization passes through object chips unchanged."""

import pytest
from industry_pack_loader import normalize_chip, normalize_chip_list


def test_normalize_chip_passes_through_object_with_id_and_label():
    """Test that objects with {id, label} pass through unchanged."""
    chip = {"id": "cleaning_exam", "label": "Cleaning + exam"}
    result = normalize_chip(chip)
    
    assert result['id'] == "cleaning_exam"
    assert result['label'] == "Cleaning + exam"


def test_normalize_chip_object_maintains_exact_id():
    """Test that the ID from object chips is preserved exactly."""
    chip = {"id": "custom_id_123", "label": "Custom Service"}
    result = normalize_chip(chip)
    
    assert result['id'] == "custom_id_123"


def test_normalize_chip_object_maintains_exact_label():
    """Test that the label from object chips is preserved exactly."""
    chip = {"id": "service", "label": "Service with Special Chars! & More"}
    result = normalize_chip(chip)
    
    assert result['label'] == "Service with Special Chars! & More"


def test_normalize_chip_list_passes_through_objects():
    """Test that normalize_chip_list preserves object chips."""
    chips = [
        {"id": "preventive", "label": "Preventive care"},
        {"id": "cosmetic", "label": "Cosmetic dentistry"},
        {"id": "emergency", "label": "Emergency care"}
    ]
    result = normalize_chip_list(chips)
    
    assert len(result) == 3
    assert result[0]['id'] == "preventive"
    assert result[1]['id'] == "cosmetic"
    assert result[2]['id'] == "emergency"


def test_normalize_chip_list_mixed_formats():
    """Test that normalize_chip_list handles mixed string and object chips."""
    chips = [
        "String chip",
        {"id": "object_chip", "label": "Object chip"},
        "Another string"
    ]
    result = normalize_chip_list(chips)
    
    assert len(result) == 3
    # All should be normalized to objects
    for chip in result:
        assert 'id' in chip
        assert 'label' in chip
    
    # Object chip should preserve its ID
    assert result[1]['id'] == "object_chip"
    assert result[1]['label'] == "Object chip"


def test_normalize_chip_object_with_only_label_generates_id():
    """Test that objects with only label get an auto-generated ID."""
    chip = {"label": "Service Name"}
    result = normalize_chip(chip)
    
    assert 'id' in result
    assert result['label'] == "Service Name"
    assert isinstance(result['id'], str)
    assert len(result['id']) > 0


def test_normalize_chip_object_with_only_id_uses_id_as_label():
    """Test that objects with only ID use ID as the label."""
    chip = {"id": "service_id"}
    result = normalize_chip(chip)
    
    assert result['id'] == "service_id"
    assert result['label'] == "service_id"


def test_normalize_chip_list_no_warning_for_objects(caplog):
    """Test that object chips don't trigger legacy format warning."""
    import logging
    
    with caplog.at_level(logging.WARNING):
        chips = [
            {"id": "chip1", "label": "Chip 1"},
            {"id": "chip2", "label": "Chip 2"}
        ]
        normalize_chip_list(chips)
    
    # Should NOT log warning about legacy format
    legacy_warnings = [r for r in caplog.records if "legacy string chips" in r.message.lower()]
    assert len(legacy_warnings) == 0


def test_normalize_chip_list_warning_only_for_strings(caplog):
    """Test that warning is logged only when strings are present."""
    import logging
    
    # Test with objects only - no warning
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        chips_objects = [
            {"id": "chip1", "label": "Chip 1"},
            {"id": "chip2", "label": "Chip 2"}
        ]
        normalize_chip_list(chips_objects)
        
        legacy_warnings = [r for r in caplog.records if "legacy string chips" in r.message.lower()]
        assert len(legacy_warnings) == 0
    
    # Test with mixed - should warn
    with caplog.at_level(logging.WARNING):
        caplog.clear()
        chips_mixed = [
            "String chip",
            {"id": "chip2", "label": "Chip 2"}
        ]
        normalize_chip_list(chips_mixed)
        
        legacy_warnings = [r for r in caplog.records if "legacy string chips" in r.message.lower()]
        assert len(legacy_warnings) > 0


def test_object_chip_id_format_preserved():
    """Test that object chip IDs preserve their format (case, underscores, etc)."""
    chips = [
        {"id": "UPPERCASE_ID", "label": "Label 1"},
        {"id": "mixed_Case_ID", "label": "Label 2"},
        {"id": "lowercase_id", "label": "Label 3"}
    ]
    result = normalize_chip_list(chips)
    
    # IDs should be preserved exactly as provided
    assert result[0]['id'] == "UPPERCASE_ID"
    assert result[1]['id'] == "mixed_Case_ID"
    assert result[2]['id'] == "lowercase_id"


def test_object_chip_label_special_characters_preserved():
    """Test that object chip labels preserve all special characters."""
    chip = {
        "id": "special_service",
        "label": "Service with $pecial Ch@rs! & More™"
    }
    result = normalize_chip(chip)
    
    assert result['label'] == "Service with $pecial Ch@rs! & More™"


def test_normalize_chip_empty_object():
    """Test that empty objects are handled gracefully."""
    chip = {}
    result = normalize_chip(chip)
    
    assert isinstance(result, dict)
    assert 'id' in result
    assert 'label' in result


def test_normalize_chip_object_extra_fields_ignored():
    """Test that extra fields in chip objects are ignored."""
    chip = {
        "id": "service_id",
        "label": "Service Label",
        "extra_field": "should be ignored",
        "another_field": 123
    }
    result = normalize_chip(chip)
    
    # Should only have id and label
    assert set(result.keys()) == {'id', 'label'}
    assert result['id'] == "service_id"
    assert result['label'] == "Service Label"
