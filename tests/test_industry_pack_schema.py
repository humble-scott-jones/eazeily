"""Test industry pack schema validation."""

import json
import os
import pytest
from pathlib import Path
from industry_pack_loader import (
    get_industry_packs_dir,
    load_industry_pack,
    validate_industry_pack,
    get_available_industry_packs,
    load_schema
)


def test_schema_exists():
    """Test that schema.json exists and is valid JSON."""
    schema = load_schema()
    assert schema, "Schema should not be empty"
    assert "$schema" in schema or "type" in schema, "Schema should have $schema or type field"


def test_all_industry_packs_are_valid_json():
    """Test that all industry pack JSON files are valid JSON."""
    packs_dir = get_industry_packs_dir()
    for pack_file in packs_dir.glob("*.json"):
        if pack_file.stem == "schema":
            continue
        
        with open(pack_file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                assert isinstance(data, dict), f"{pack_file.name} should contain a JSON object"
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON in {pack_file.name}: {e}")


def test_required_industry_packs_exist():
    """Test that all required industry packs exist."""
    required_packs = ['salon', 'dentist', 'gym', 'cleaner']
    available_packs = get_available_industry_packs()
    
    for pack_id in required_packs:
        assert pack_id in available_packs, f"Industry pack '{pack_id}' should exist"


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_industry_pack_has_required_fields(industry_id):
    """Test that each industry pack has all required fields."""
    pack = load_industry_pack(industry_id)
    assert pack is not None, f"Failed to load {industry_id} pack"
    
    required_fields = [
        "id",
        "display_name",
        "primary_customer_goal",
        "version",
        "business_profile_fields",
        "default_channel_strategy",
        "keyword_banks",
        "cta_library",
        "compliance_safety_rules",
        "content_templates",
        "example_outputs",
        "prompt_integration_hooks"
    ]
    
    for field in required_fields:
        assert field in pack, f"{industry_id} pack missing required field: {field}"


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_industry_pack_validation(industry_id):
    """Test that each industry pack passes validation."""
    pack = load_industry_pack(industry_id)
    assert pack is not None
    
    errors = validate_industry_pack(pack)
    assert len(errors) == 0, f"{industry_id} pack has validation errors: {errors}"


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_keyword_banks_structure(industry_id):
    """Test keyword banks have correct structure."""
    pack = load_industry_pack(industry_id)
    assert pack is not None
    
    kb = pack.get('keyword_banks', {})
    
    # Check seed_keywords
    assert 'seed_keywords' in kb, f"{industry_id} missing seed_keywords"
    assert isinstance(kb['seed_keywords'], list), "seed_keywords should be a list"
    assert len(kb['seed_keywords']) >= 10, f"{industry_id} should have at least 10 seed keywords"
    
    # Check topic_clusters
    assert 'topic_clusters' in kb, f"{industry_id} missing topic_clusters"
    assert isinstance(kb['topic_clusters'], list), "topic_clusters should be a list"
    assert len(kb['topic_clusters']) > 0, f"{industry_id} should have at least one topic cluster"
    
    for cluster in kb['topic_clusters']:
        assert 'name' in cluster, "Topic cluster missing name"
        assert 'intent' in cluster, "Topic cluster missing intent"
        assert cluster['intent'] in ['awareness', 'conversion', 'retention'], \
            f"Invalid intent: {cluster['intent']}"
        assert 'examples' in cluster, "Topic cluster missing examples"
        assert isinstance(cluster['examples'], list), "Topic cluster examples should be a list"
    
    # Check seasonal_hooks
    assert 'seasonal_hooks' in kb, f"{industry_id} missing seasonal_hooks"
    assert isinstance(kb['seasonal_hooks'], list), "seasonal_hooks should be a list"


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_cta_library_structure(industry_id):
    """Test CTA library has correct structure."""
    pack = load_industry_pack(industry_id)
    assert pack is not None
    
    cta_lib = pack.get('cta_library', {})
    required_cta_types = ['booking_ctas', 'inquiry_ctas', 'review_referral_ctas', 'offer_ctas']
    
    for cta_type in required_cta_types:
        assert cta_type in cta_lib, f"{industry_id} missing {cta_type}"
        assert isinstance(cta_lib[cta_type], list), f"{cta_type} should be a list"
        assert len(cta_lib[cta_type]) >= 3, f"{industry_id} {cta_type} should have at least 3 items"
        
        # Check that CTAs are strings and not empty
        for cta in cta_lib[cta_type]:
            assert isinstance(cta, str), f"CTA should be a string: {cta}"
            assert len(cta.strip()) > 0, "CTA should not be empty"


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_compliance_rules_structure(industry_id):
    """Test compliance and safety rules have correct structure."""
    pack = load_industry_pack(industry_id)
    assert pack is not None
    
    compliance = pack.get('compliance_safety_rules', {})
    required_fields = ['forbidden_claims', 'privacy_constraints', 'regulated_language_notes', 'do_not_generate']
    
    for field in required_fields:
        assert field in compliance, f"{industry_id} compliance missing {field}"
        assert isinstance(compliance[field], list), f"{field} should be a list"
        # At least one item in each compliance section
        assert len(compliance[field]) > 0, f"{industry_id} {field} should not be empty"


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_content_templates_structure(industry_id):
    """Test content templates have correct structure."""
    pack = load_industry_pack(industry_id)
    assert pack is not None
    
    templates = pack.get('content_templates', {})
    
    # Check social_templates
    assert 'social_templates' in templates, f"{industry_id} missing social_templates"
    social = templates['social_templates']
    assert 'post_structures' in social, "Missing post_structures"
    assert 'reel_structures' in social, "Missing reel_structures"
    assert 'content_angles' in social, "Missing content_angles"
    
    # Check email_templates
    assert 'email_templates' in templates, f"{industry_id} missing email_templates"
    email = templates['email_templates']
    assert 'scenarios' in email, "Missing email scenarios"
    assert len(email['scenarios']) > 0, "Should have at least one email scenario"
    
    for scenario in email['scenarios']:
        assert 'name' in scenario, "Email scenario missing name"
        assert 'required_fields' in scenario, "Email scenario missing required_fields"
        assert 'recommended_tone' in scenario, "Email scenario missing recommended_tone"
        assert 'suggested_cta' in scenario, "Email scenario missing suggested_cta"
    
    # Check review_reply_guidelines
    assert 'review_reply_guidelines' in templates, f"{industry_id} missing review_reply_guidelines"
    review = templates['review_reply_guidelines']
    assert 'channel_specific' in review, "Missing channel_specific"
    assert 'empathy_patterns' in review, "Missing empathy_patterns"
    assert 'compliance_notes' in review, "Missing compliance_notes"


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_example_outputs_structure(industry_id):
    """Test example outputs have correct structure."""
    pack = load_industry_pack(industry_id)
    assert pack is not None
    
    examples = pack.get('example_outputs', {})
    required_examples = ['social_post', 'reel_script', 'email', 'review_reply']
    
    for example_type in required_examples:
        assert example_type in examples, f"{industry_id} missing {example_type} example"
        assert isinstance(examples[example_type], dict), f"{example_type} should be a dict"
        assert len(examples[example_type]) > 0, f"{example_type} should not be empty"


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_prompt_integration_hooks_structure(industry_id):
    """Test prompt integration hooks have correct structure."""
    pack = load_industry_pack(industry_id)
    assert pack is not None
    
    hooks = pack.get('prompt_integration_hooks', {})
    
    assert 'industry_pack_id' in hooks, f"{industry_id} missing industry_pack_id"
    assert hooks['industry_pack_id'] == industry_id, "industry_pack_id should match pack id"
    
    assert 'constraints_for_model' in hooks, f"{industry_id} missing constraints_for_model"
    assert isinstance(hooks['constraints_for_model'], list), "constraints_for_model should be a list"
    assert len(hooks['constraints_for_model']) > 0, "Should have at least one constraint"
    
    assert 'default_do_dont_list' in hooks, f"{industry_id} missing default_do_dont_list"
    do_dont = hooks['default_do_dont_list']
    assert 'do' in do_dont, "Missing 'do' list"
    assert 'dont' in do_dont, "Missing 'dont' list"
    assert isinstance(do_dont['do'], list), "'do' should be a list"
    assert isinstance(do_dont['dont'], list), "'dont' should be a list"
    assert len(do_dont['do']) > 0, "Should have at least one 'do' item"
    assert len(do_dont['dont']) > 0, "Should have at least one 'dont' item"


def test_version_format():
    """Test that all packs use valid semantic versioning."""
    import re
    version_pattern = re.compile(r'^\d+\.\d+\.\d+$')
    
    for industry_id in ['salon', 'dentist', 'gym', 'cleaner']:
        pack = load_industry_pack(industry_id)
        assert pack is not None
        
        version = pack.get('version', '')
        assert version_pattern.match(version), \
            f"{industry_id} has invalid version format: {version} (expected X.Y.Z)"


def test_primary_customer_goal_valid():
    """Test that primary_customer_goal uses valid values."""
    valid_goals = ['bookings', 'memberships', 'recurring_clients', 'sales', 'leads']
    
    for industry_id in ['salon', 'dentist', 'gym', 'cleaner']:
        pack = load_industry_pack(industry_id)
        assert pack is not None
        
        goal = pack.get('primary_customer_goal', '')
        assert goal in valid_goals, \
            f"{industry_id} has invalid primary_customer_goal: {goal}"
