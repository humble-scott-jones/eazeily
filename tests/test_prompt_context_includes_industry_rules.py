"""Test that prompt context includes industry-specific rules and constraints."""

import pytest
from services.generation.prompt_compiler import PromptCompiler, ProfileDefaults, RunToggles


@pytest.mark.parametrize("industry_id,industry_name", [
    ('salon', 'Salon'),
    ('dentist', 'Dentist'),
    ('gym', 'Gym'),
    ('cleaner', 'Cleaner'),
])
def test_industry_pack_constraints_in_context(industry_id, industry_name):
    """Test that industry pack constraints are included in model context."""
    # Create a profile with an industry that has a pack
    profile = ProfileDefaults(
        company="Test Company",
        industry=industry_name,
        signature_tone="professional",
        platforms=["instagram", "facebook"]
    )
    
    # Create run toggles
    toggles = RunToggles(
        session_length=7,
        platform_focus=["instagram"],
        keywords=["test"],
        goals=["engagement"]
    )
    
    # Compile prompt
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles)
    
    # Check that industry_pack_id is set
    model_context = output['model_context']
    assert model_context.get('industry_pack_id') == industry_id, \
        f"Expected industry_pack_id to be '{industry_id}'"
    
    # Check that industry_constraints are included
    assert 'industry_constraints' in model_context, "Should have industry_constraints"
    constraints = model_context['industry_constraints']
    assert constraints is not None, "Constraints should not be None"
    
    # Check that do/don't lists are present
    assert 'do' in constraints, "Should have 'do' list"
    assert 'dont' in constraints, "Should have 'dont' list"
    assert len(constraints['do']) > 0, "Should have at least one 'do' constraint"
    assert len(constraints['dont']) > 0, "Should have at least one 'dont' constraint"


@pytest.mark.parametrize("industry_id,industry_name", [
    ('salon', 'Salon'),
    ('dentist', 'Dentist'),
    ('gym', 'Gym'),
    ('cleaner', 'Cleaner'),
])
def test_industry_constraints_in_prompt_text(industry_id, industry_name):
    """Test that industry constraints appear in the generated prompt text."""
    profile = ProfileDefaults(
        company="Test Company",
        industry=industry_name,
        signature_tone="professional",
        platforms=["instagram"]
    )
    
    toggles = RunToggles(
        session_length=3,
        platform_focus=["instagram"],
        keywords=["test"]
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles)
    
    # Check that prompt includes industry guidelines
    prompt_set = output['prompt_set']
    context_section = prompt_set['context']
    
    # Should mention industry guidelines
    assert 'INDUSTRY GUIDELINES' in context_section or industry_id in context_section.lower(), \
        f"Prompt should mention industry guidelines for {industry_name}"
    
    # Should include DO/DON'T markers
    assert '✓ DO:' in context_section or 'DO:' in context_section, \
        "Prompt should include DO constraints"
    assert '✗ DON\'T:' in context_section or 'DON\'T:' in context_section, \
        "Prompt should include DON'T constraints"


def test_industry_without_pack_has_no_constraints():
    """Test that industries without packs don't have industry_pack_id or constraints."""
    # Use an industry that doesn't have a pack
    profile = ProfileDefaults(
        company="Test Company",
        industry="Restaurant",
        signature_tone="friendly",
        platforms=["facebook"]
    )
    
    toggles = RunToggles(
        session_length=5,
        platform_focus=["facebook"],
        keywords=["food"]
    )
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles)
    
    model_context = output['model_context']
    
    # Should not have industry_pack_id set
    assert model_context.get('industry_pack_id') is None, \
        "Industries without packs should not have industry_pack_id"
    
    # Should not have industry_constraints or they should be None/empty
    constraints = model_context.get('industry_constraints')
    if constraints:
        assert not constraints.get('do') and not constraints.get('dont'), \
            "Industries without packs should not have constraints"


@pytest.mark.parametrize("industry_name,expected_pack_id", [
    ('Salon', 'salon'),
    ('Hair Studio', 'salon'),
    ('Dentist', 'dentist'),
    ('Dental Practice', 'dentist'),
    ('Gym', 'gym'),
    ('Fitness Center', 'gym'),
    ('Cleaner', 'cleaner'),
    ('Cleaning Service', 'cleaner'),
])
def test_industry_name_mapping_to_packs(industry_name, expected_pack_id):
    """Test that various industry names map correctly to industry packs."""
    profile = ProfileDefaults(
        company="Test Company",
        industry=industry_name,
        signature_tone="professional",
        platforms=["instagram"]
    )
    
    toggles = RunToggles(session_length=3, platform_focus=["instagram"])
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles)
    
    model_context = output['model_context']
    
    # Should map to the expected pack
    assert model_context.get('industry_pack_id') == expected_pack_id, \
        f"'{industry_name}' should map to pack '{expected_pack_id}'"


def test_industry_constraints_precedence_with_voice():
    """Test that industry constraints work alongside voice fingerprint."""
    from services.generation.prompt_compiler import VoiceFingerprint
    
    profile = ProfileDefaults(
        company="Salon XYZ",
        industry="Salon",
        signature_tone="friendly",
        platforms=["instagram"]
    )
    
    voice = VoiceFingerprint(
        sentence_length_band="short",
        top_phrases=["gorgeous", "stunning", "transformation"],
        avoid_phrases=["cheap", "discount"],
        typical_cta_patterns=["Book today!", "DM us"]
    )
    
    toggles = RunToggles(session_length=3, platform_focus=["instagram"])
    
    compiler = PromptCompiler(profile_defaults=profile, voice_fingerprint=voice)
    output = compiler.compile_for_social(toggles)
    
    model_context = output['model_context']
    prompt_set = output['prompt_set']
    
    # Should have both industry constraints and voice style
    assert model_context.get('industry_pack_id') == 'salon'
    assert model_context.get('industry_constraints') is not None
    assert model_context.get('voice_applied') is True
    assert model_context.get('voice_style') is not None
    
    # Prompt should include both
    context = prompt_set['context']
    assert 'INDUSTRY GUIDELINES' in context, "Should include industry guidelines"
    assert 'VOICE STYLE' in context, "Should include voice style"


def test_trace_summary_includes_industry_info():
    """Test that trace summary includes industry pack information."""
    profile = ProfileDefaults(
        company="Dental Care",
        industry="Dentist",
        signature_tone="professional",
        platforms=["google", "facebook"]
    )
    
    toggles = RunToggles(session_length=5, platform_focus=["google"])
    
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles, request_id="test-123")
    
    trace = output['trace_summary']
    
    # Trace should include request info
    assert 'request_id' in trace
    assert trace['request_id'] == 'test-123'
    
    # Model context should have industry info
    model_ctx = output['model_context']
    assert 'industry' in model_ctx
    assert model_ctx['industry'] == 'Dentist'
    assert model_ctx.get('industry_pack_id') == 'dentist'


def test_dentist_compliance_prevents_medical_claims():
    """Test that dentist industry has specific compliance constraints."""
    from industry_pack_loader import get_industry_compliance_rules
    
    rules = get_industry_compliance_rules('dentist')
    assert rules, "Dentist should have compliance rules"
    
    # Check for HIPAA-related constraints
    forbidden = rules.get('forbidden_claims', [])
    privacy = rules.get('privacy_constraints', [])
    do_not_gen = rules.get('do_not_generate', [])
    
    # Should have restrictions on medical claims
    assert any('HIPAA' in str(item).upper() or 'medical' in str(item).lower() 
               for item in privacy + do_not_gen), \
        "Dentist should have HIPAA/medical privacy constraints"
    
    # Should prevent guarantees
    assert any('guarantee' in str(item).lower() for item in forbidden), \
        "Dentist should prevent guaranteed outcome claims"


def test_salon_compliance_prevents_guarantee_claims():
    """Test that salon industry has transformation-specific compliance."""
    from industry_pack_loader import get_industry_compliance_rules
    
    rules = get_industry_compliance_rules('salon')
    assert rules, "Salon should have compliance rules"
    
    forbidden = rules.get('forbidden_claims', [])
    privacy = rules.get('privacy_constraints', [])
    
    # Should require consent for before/after
    assert any('consent' in str(item).lower() or 'permission' in str(item).lower() 
               for item in forbidden + privacy), \
        "Salon should require consent for transformations"


def test_gym_compliance_prevents_body_guarantees():
    """Test that gym industry has fitness-specific compliance."""
    from industry_pack_loader import get_industry_compliance_rules
    
    rules = get_industry_compliance_rules('gym')
    assert rules, "Gym should have compliance rules"
    
    forbidden = rules.get('forbidden_claims', [])
    regulated = rules.get('regulated_language_notes', [])
    
    # Should prevent weight loss guarantees
    assert any('guarantee' in str(item).lower() or 'weight loss' in str(item).lower() 
               for item in forbidden + regulated), \
        "Gym should prevent weight/body transformation guarantees"
    
    # Should mention results vary
    assert any('results may vary' in str(item).lower() for item in regulated), \
        "Gym should require 'results may vary' disclaimer"
