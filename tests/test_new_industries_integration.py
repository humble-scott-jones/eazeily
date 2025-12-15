"""Integration tests for new industry packs in the full generation flow."""

import pytest
from datetime import date


@pytest.mark.parametrize("industry_name", [
    "Salon",
    "Dentist", 
    "Gym",
    "Cleaner"
])
def test_new_industry_generates_posts_with_constraints(industry_name):
    """Test that new industries can generate posts with industry-specific constraints."""
    from generator import generate_posts
    
    # Generate posts for each new industry
    posts = generate_posts(
        days=3,
        start_day=date.today(),
        industry=industry_name,
        tone='professional',
        platforms=['instagram', 'facebook'],
        brand_keywords=['quality', 'local'],
        include_images=False,
        niche_keywords=['service', 'professional'],
        goals=['engagement', 'bookings'],
        company=f"{industry_name} Test Co"
    )
    
    # Should generate posts
    assert len(posts) > 0, f"Should generate posts for {industry_name}"
    assert len(posts) == 6, f"Expected 6 posts (3 days × 2 platforms), got {len(posts)}"
    
    # Each post should have required fields
    for post in posts:
        assert 'caption' in post, "Post should have caption"
        assert 'platform' in post, "Post should have platform"
        assert 'pillar' in post, "Post should have pillar"
        assert 'date' in post, "Post should have date"
        
        # Caption should be non-empty
        assert len(post['caption'].strip()) > 0, "Caption should not be empty"


@pytest.mark.parametrize("industry_name", [
    "Salon",
    "Dentist",
    "Gym", 
    "Cleaner"
])
def test_new_industry_in_config_json(industry_name):
    """Test that new industries appear in config.json."""
    import json
    import os
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'content', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    industries = config.get('industries', [])
    industry_keys = [ind.get('key', '').lower() for ind in industries]
    
    # Map industry name to expected key
    key_map = {
        'Salon': 'salon',
        'Dentist': 'dentist',
        'Gym': 'gym',
        'Cleaner': 'cleaner'
    }
    
    expected_key = key_map.get(industry_name)
    assert expected_key in industry_keys, \
        f"{industry_name} (key: {expected_key}) should be in config.json industries"
    
    # Find the industry entry
    industry_entry = next((ind for ind in industries if ind.get('key') == expected_key), None)
    assert industry_entry is not None, f"Should find {expected_key} in industries"
    
    # Check required fields
    assert 'label' in industry_entry, f"{expected_key} should have label"
    assert 'icon' in industry_entry, f"{expected_key} should have icon"
    assert 'suggested_keywords' in industry_entry, f"{expected_key} should have suggested_keywords"
    assert 'note_placeholder' in industry_entry, f"{expected_key} should have note_placeholder"
    
    # Check keywords
    assert len(industry_entry['suggested_keywords']) > 0, \
        f"{expected_key} should have at least one suggested keyword"


@pytest.mark.parametrize("industry_name,expected_key", [
    ("Salon", "salon"),
    ("Dentist", "dentist"),
    ("Gym", "gym"),
    ("Cleaner", "cleaner")
])
def test_new_industry_has_questions(industry_name, expected_key):
    """Test that new industries have wizard questions configured."""
    import json
    import os
    
    config_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'content', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    questions = config.get('questions', {})
    assert expected_key in questions, f"{expected_key} should have questions configured"
    
    industry_questions = questions[expected_key]
    assert len(industry_questions) > 0, f"{expected_key} should have at least one question"
    
    # Check question structure
    for q in industry_questions:
        assert 'type' in q, "Question should have type"
        assert 'key' in q, "Question should have key"
        assert 'label' in q, "Question should have label"
        
        if q['type'] == 'chips':
            assert 'options' in q, "Chips question should have options"
            assert len(q['options']) > 0, "Chips question should have at least one option"


def test_industry_pack_loader_can_load_all_new_industries():
    """Test that industry_pack_loader can successfully load all new industry packs."""
    from industry_pack_loader import load_industry_pack, get_available_industry_packs
    
    # Check that all new industries are available
    available = get_available_industry_packs()
    for industry_id in ['salon', 'dentist', 'gym', 'cleaner']:
        assert industry_id in available, f"{industry_id} should be in available packs"
        
        # Try to load each pack
        pack = load_industry_pack(industry_id)
        assert pack is not None, f"Should be able to load {industry_id} pack"
        assert pack.get('id') == industry_id, f"Pack id should match {industry_id}"


def test_salon_compliance_rules_included_in_generation():
    """Test that salon-specific compliance rules are properly integrated."""
    from services.generation.prompt_compiler import PromptCompiler, ProfileDefaults, RunToggles
    
    profile = ProfileDefaults(
        company="Salon Test",
        industry="Salon",
        signature_tone="friendly",
        platforms=["instagram"]
    )
    
    toggles = RunToggles(
        session_length=3,
        platform_focus=["instagram"],
        keywords=["hair", "transformation"]
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles)
    
    # Check that salon constraints are included
    context = output['model_context']
    assert context.get('industry_pack_id') == 'salon'
    constraints = context.get('industry_constraints', {})
    
    # Check for salon-specific constraints
    do_list = constraints.get('do', [])
    dont_list = constraints.get('dont', [])
    
    # Salon should emphasize transformations
    assert any('transformation' in item.lower() for item in do_list), \
        "Salon should emphasize transformations"
    
    # Salon should avoid guarantees
    assert any('guarantee' in item.lower() for item in dont_list), \
        "Salon should avoid guaranteeing results"


def test_dentist_hipaa_compliance_included():
    """Test that dentist-specific HIPAA compliance rules are properly integrated."""
    from services.generation.prompt_compiler import PromptCompiler, ProfileDefaults, RunToggles
    
    profile = ProfileDefaults(
        company="Dental Practice",
        industry="Dentist",
        signature_tone="professional",
        platforms=["google", "facebook"]
    )
    
    toggles = RunToggles(
        session_length=5,
        platform_focus=["facebook"],
        keywords=["dental health", "checkup"]
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles)
    
    # Check that dentist constraints are included
    context = output['model_context']
    assert context.get('industry_pack_id') == 'dentist'
    constraints = context.get('industry_constraints', {})
    
    # Dentist should have compliance-focused constraints
    dont_list = constraints.get('dont', [])
    
    # Should avoid medical claims/diagnoses
    has_medical_constraint = any(
        'medical' in item.lower() or 'diagnos' in item.lower() or 'guarantee' in item.lower()
        for item in dont_list
    )
    assert has_medical_constraint, "Dentist should have medical/diagnostic constraints"


def test_gym_results_disclaimer_included():
    """Test that gym-specific 'results may vary' compliance is included."""
    from services.generation.prompt_compiler import PromptCompiler, ProfileDefaults, RunToggles
    from industry_pack_loader import get_industry_compliance_rules
    
    # Check compliance rules directly
    rules = get_industry_compliance_rules('gym')
    assert rules, "Gym should have compliance rules"
    
    regulated_notes = rules.get('regulated_language_notes', [])
    
    # Should include results vary disclaimer
    has_disclaimer = any('results may vary' in note.lower() for note in regulated_notes)
    assert has_disclaimer, "Gym should require 'results may vary' disclaimer"
    
    # Check in prompt compilation
    profile = ProfileDefaults(
        company="Fitness Center",
        industry="Gym",
        signature_tone="friendly",
        platforms=["instagram", "tiktok"]
    )
    
    toggles = RunToggles(
        session_length=3,
        platform_focus=["instagram"]
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles)
    
    context = output['model_context']
    assert context.get('industry_pack_id') == 'gym'


def test_cleaner_transformation_focus():
    """Test that cleaner industry emphasizes before/after transformations."""
    from industry_pack_loader import get_default_platforms, get_topic_clusters
    
    # Check default platforms
    platforms = get_default_platforms('cleaner')
    assert 'instagram' in platforms or 'facebook' in platforms, \
        "Cleaner should use visual platforms"
    
    # Check topic clusters
    clusters = get_topic_clusters('cleaner')
    cluster_names = [c.get('name', '').lower() for c in clusters]
    
    # Should have transformation-related cluster
    has_transformation = any('transformation' in name or 'before' in name for name in cluster_names)
    assert has_transformation, "Cleaner should have transformation content cluster"
