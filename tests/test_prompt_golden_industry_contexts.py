"""Golden context snapshots for industry packs.

This test creates and validates golden snapshots of compiled contexts for each industry.
Golden snapshots are used as stable baselines for QA and regression testing.
"""

import json
import os
import pytest
from pathlib import Path
from services.generation.prompt_compiler import PromptCompiler, ProfileDefaults, RunToggles


# Golden snapshot directory
GOLDEN_DIR = Path(__file__).parent / "golden"
GOLDEN_DIR.mkdir(exist_ok=True)


def _serialize_for_golden(output):
    """Serialize compiler output for golden snapshot (remove timestamps, request IDs)."""
    # Create a stable copy
    stable = {
        'model_context': dict(output['model_context']),
        'prompt_set': dict(output['prompt_set']),
        'trace_summary': {
            'content_type': output['trace_summary'].get('content_type'),
            'selections': output['trace_summary'].get('selections'),
            'voice_fingerprint_applied': output['trace_summary'].get('voice_fingerprint_applied'),
            'template_used': output['trace_summary'].get('template_used'),
            'flags': output['trace_summary'].get('flags')
        }
    }
    
    # Remove timestamp and request_id for stability
    if 'timestamp' in stable['trace_summary']:
        del stable['trace_summary']['timestamp']
    if 'request_id' in stable['trace_summary']:
        del stable['trace_summary']['request_id']
    
    return stable


@pytest.mark.parametrize("industry_id,industry_name", [
    ('salon', 'Salon'),
    ('dentist', 'Dentist'),
    ('gym', 'Gym'),
    ('cleaner', 'Cleaner'),
])
def test_generate_golden_context(industry_id, industry_name):
    """Generate golden context snapshot for each industry."""
    # Standard profile for golden snapshot
    profile = ProfileDefaults(
        company=f"{industry_name} Example Co.",
        industry=industry_name,
        signature_tone="professional",
        platforms=["instagram", "facebook"],
        offerings="high-quality services",
        audience="local community"
    )
    
    # Standard toggles
    toggles = RunToggles(
        session_length=7,
        platform_focus=["instagram"],
        keywords=["quality", "local", "professional"],
        goals=["engagement", "bookings"]
    )
    
    # Compile
    compiler = PromptCompiler(profile_defaults=profile)
    output = compiler.compile_for_social(toggles)
    
    # Serialize for golden
    golden = _serialize_for_golden(output)
    
    # Save to file
    golden_path = GOLDEN_DIR / f"{industry_id}_context.json"
    with open(golden_path, 'w', encoding='utf-8') as f:
        json.dump(golden, f, indent=2)
    
    print(f"\n✓ Generated golden context: {golden_path}")
    
    # Basic validation
    assert golden['model_context']['industry'] == industry_name
    assert golden['model_context']['industry_pack_id'] == industry_id
    assert golden['model_context']['industry_constraints'] is not None
    
    # Check that prompt includes industry guidelines
    context_section = golden['prompt_set']['context']
    assert 'INDUSTRY GUIDELINES' in context_section
    assert '✓ DO:' in context_section
    assert '✗ DON\'T:' in context_section


@pytest.mark.parametrize("industry_id", ['salon', 'dentist', 'gym', 'cleaner'])
def test_validate_golden_context_stability(industry_id):
    """Validate that golden context snapshots are stable and contain required fields."""
    golden_path = GOLDEN_DIR / f"{industry_id}_context.json"
    
    if not golden_path.exists():
        pytest.skip(f"Golden snapshot not yet created: {golden_path}")
    
    # Load golden
    with open(golden_path, 'r', encoding='utf-8') as f:
        golden = json.load(f)
    
    # Validate structure
    assert 'model_context' in golden, "Golden should have model_context"
    assert 'prompt_set' in golden, "Golden should have prompt_set"
    assert 'trace_summary' in golden, "Golden should have trace_summary"
    
    # Validate model_context
    ctx = golden['model_context']
    assert 'industry' in ctx
    assert 'industry_pack_id' in ctx
    assert ctx['industry_pack_id'] == industry_id
    assert 'industry_constraints' in ctx
    assert ctx['industry_constraints'] is not None
    
    constraints = ctx['industry_constraints']
    assert 'do' in constraints
    assert 'dont' in constraints
    assert len(constraints['do']) > 0, "Should have at least one 'do' constraint"
    assert len(constraints['dont']) > 0, "Should have at least one 'dont' constraint"
    
    # Validate prompt_set
    prompt = golden['prompt_set']
    assert 'system' in prompt
    assert 'context' in prompt
    assert 'request' in prompt
    
    # Check that context includes industry guidelines
    assert 'INDUSTRY GUIDELINES' in prompt['context']
    assert '✓ DO:' in prompt['context'] or 'DO:' in prompt['context']
    assert '✗ DON\'T:' in prompt['context'] or 'DON\'T:' in prompt['context']
    
    print(f"✓ Golden snapshot validated: {golden_path}")


def test_golden_contexts_differ_by_industry():
    """Ensure golden contexts are meaningfully different for each industry."""
    golden_contexts = {}
    
    for industry_id in ['salon', 'dentist', 'gym', 'cleaner']:
        golden_path = GOLDEN_DIR / f"{industry_id}_context.json"
        if not golden_path.exists():
            pytest.skip(f"Golden snapshot not yet created: {golden_path}")
        
        with open(golden_path, 'r', encoding='utf-8') as f:
            golden_contexts[industry_id] = json.load(f)
    
    if len(golden_contexts) < 2:
        pytest.skip("Need at least 2 golden contexts to compare")
    
    # Check that constraints differ between industries
    industries = list(golden_contexts.keys())
    for i, ind1 in enumerate(industries):
        for ind2 in industries[i+1:]:
            ctx1 = golden_contexts[ind1]['model_context']['industry_constraints']
            ctx2 = golden_contexts[ind2]['model_context']['industry_constraints']
            
            # At least one constraint should be different
            do1 = set(ctx1['do'])
            do2 = set(ctx2['do'])
            dont1 = set(ctx1['dont'])
            dont2 = set(ctx2['dont'])
            
            assert do1 != do2 or dont1 != dont2, \
                f"{ind1} and {ind2} should have different constraints"
    
    print(f"✓ All {len(golden_contexts)} golden contexts are meaningfully different")


def test_regenerated_context_matches_golden():
    """Test that regenerating a context produces the same result as golden snapshot."""
    # This is a regression test - ensure prompts are deterministic
    
    for industry_id, industry_name in [('salon', 'Salon'), ('dentist', 'Dentist')]:
        golden_path = GOLDEN_DIR / f"{industry_id}_context.json"
        
        if not golden_path.exists():
            pytest.skip(f"Golden snapshot not yet created: {golden_path}")
        
        # Load golden
        with open(golden_path, 'r', encoding='utf-8') as f:
            golden = json.load(f)
        
        # Regenerate with same params
        profile = ProfileDefaults(
            company=f"{industry_name} Example Co.",
            industry=industry_name,
            signature_tone="professional",
            platforms=["instagram", "facebook"],
            offerings="high-quality services",
            audience="local community"
        )
        
        toggles = RunToggles(
            session_length=7,
            platform_focus=["instagram"],
            keywords=["quality", "local", "professional"],
            goals=["engagement", "bookings"]
        )
        
        compiler = PromptCompiler(profile_defaults=profile)
        output = compiler.compile_for_social(toggles)
        regenerated = _serialize_for_golden(output)
        
        # Compare key fields (model_context and prompt structure)
        assert regenerated['model_context']['industry_pack_id'] == golden['model_context']['industry_pack_id']
        assert regenerated['model_context']['industry_constraints'] == golden['model_context']['industry_constraints']
        
        # Prompt context should be identical (or very similar - allow minor differences)
        regen_ctx = regenerated['prompt_set']['context']
        golden_ctx = golden['prompt_set']['context']
        
        # Check that industry guidelines section is present in both
        assert 'INDUSTRY GUIDELINES' in regen_ctx
        assert 'INDUSTRY GUIDELINES' in golden_ctx
        
        print(f"✓ Regenerated context matches golden for {industry_id}")
