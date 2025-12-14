"""Test that chip normalization accepts legacy string format."""

import pytest
from industry_pack_loader import normalize_chip, normalize_chip_list, generate_chip_id


def test_normalize_chip_accepts_string():
    """Test that normalize_chip accepts a string and returns {id, label}."""
    chip = "Teeth cleaning"
    result = normalize_chip(chip)
    
    assert isinstance(result, dict)
    assert 'id' in result
    assert 'label' in result
    assert result['label'] == "Teeth cleaning"
    assert isinstance(result['id'], str)
    assert len(result['id']) > 0


def test_normalize_chip_generates_stable_id():
    """Test that the same string generates the same ID."""
    chip1 = normalize_chip("Cleaning + exam")
    chip2 = normalize_chip("Cleaning + exam")
    
    assert chip1['id'] == chip2['id']
    assert chip1['label'] == chip2['label']


def test_normalize_chip_id_is_lowercase_with_underscores():
    """Test that generated IDs are lowercase with underscores."""
    chip = normalize_chip("Teeth Cleaning & Whitening")
    
    assert chip['id'].islower() or '_' in chip['id'] or chip['id'].isdigit()
    assert ' ' not in chip['id']
    assert '&' not in chip['id']
    assert '+' not in chip['id']


def test_normalize_chip_list_accepts_all_strings():
    """Test that normalize_chip_list handles a list of strings."""
    chips = ["Routine cleanings", "Preventive care", "Cosmetic dentistry"]
    result = normalize_chip_list(chips)
    
    assert len(result) == 3
    for chip in result:
        assert isinstance(chip, dict)
        assert 'id' in chip
        assert 'label' in chip


def test_normalize_chip_list_generates_unique_ids():
    """Test that all chips get unique IDs even with similar labels."""
    chips = ["Service", "Service", "Service"]
    result = normalize_chip_list(chips)
    
    ids = [chip['id'] for chip in result]
    assert len(set(ids)) == 3, "All chips should have unique IDs"


def test_generate_chip_id_basic():
    """Test basic chip ID generation."""
    chip_id = generate_chip_id("Cleaning + exam")
    
    assert chip_id == "cleaning_exam"


def test_generate_chip_id_handles_special_chars():
    """Test that special characters are converted to underscores."""
    chip_id = generate_chip_id("Teeth & Gums Care!")
    
    assert 'teeth' in chip_id
    assert 'gums' in chip_id
    assert '&' not in chip_id
    assert '!' not in chip_id


def test_generate_chip_id_collision_appends_hash():
    """Test that collisions are handled by appending a hash suffix."""
    existing_ids = {"cleaning_exam"}
    chip_id = generate_chip_id("Cleaning + exam", existing_ids)
    
    # Should append hash because "cleaning_exam" already exists
    assert chip_id != "cleaning_exam"
    assert chip_id.startswith("cleaning_exam_")


def test_normalize_chip_list_handles_collision():
    """Test that normalize_chip_list handles duplicate labels."""
    chips = ["Same Label", "Different Label", "Same Label"]
    result = normalize_chip_list(chips)
    
    # All should normalize successfully
    assert len(result) == 3
    
    # IDs should be unique
    ids = [chip['id'] for chip in result]
    assert len(set(ids)) == 3


def test_legacy_string_format_warning_logged(caplog):
    """Test that using string chips logs a warning."""
    import logging
    
    with caplog.at_level(logging.WARNING):
        chips = ["String chip 1", "String chip 2"]
        normalize_chip_list(chips)
    
    # Should log warning about legacy format
    assert any("legacy string chips" in record.message.lower() for record in caplog.records)


def test_normalize_empty_string():
    """Test that empty strings are handled gracefully."""
    chip = normalize_chip("")
    
    assert isinstance(chip, dict)
    assert 'id' in chip
    assert 'label' in chip
    assert chip['label'] == ""


def test_normalize_chip_with_numbers():
    """Test that chips with numbers are normalized correctly."""
    chip = normalize_chip("5-star reviews")
    
    assert chip['label'] == "5-star reviews"
    assert '5' in chip['id']
    assert 'star' in chip['id']


def test_normalize_chip_removes_multiple_spaces():
    """Test that multiple spaces are collapsed into single underscores."""
    chip = normalize_chip("Very    long    spacing")
    
    # Should not have multiple consecutive underscores
    assert '__' not in chip['id']


def test_normalize_chip_strips_leading_trailing_underscores():
    """Test that leading/trailing underscores are removed."""
    chip = normalize_chip("  Leading and trailing spaces  ")
    
    # ID should not start or end with underscore
    assert not chip['id'].startswith('_')
    assert not chip['id'].endswith('_')
