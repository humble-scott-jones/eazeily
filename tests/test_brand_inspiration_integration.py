"""Integration test for brand inspiration feature end-to-end."""

import pytest
from services.generation.prompt_compiler import PromptCompiler, ProfileDefaults, RunToggles


def test_brand_inspiration_full_workflow(client):
    """Test complete workflow: save inspirations → retrieve → use in generation."""
    
    # Step 1: Save brand inspirations via API
    response = client.post('/api/profile', json={
        'company': 'EcoStore',
        'industry': 'retail',
        'tone': 'friendly',
        'platforms': ['instagram', 'facebook'],
        'brand_inspirations': [
            {'name': 'Patagonia', 'why': 'authentic and mission-driven'},
            {'name': 'Allbirds', 'why': 'simple and sustainable messaging'}
        ],
        'brand_anti_inspirations': [
            {'name': 'Fast Fashion Co', 'why': 'too salesy and inauthentic'}
        ]
    })
    
    assert response.status_code == 200
    assert response.get_json()['ok'] is True
    
    # Step 2: Retrieve profile
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = response.get_json()
    profile = data['profile']
    
    # Verify inspirations were saved
    assert len(profile['brand_inspirations']) == 2
    assert profile['brand_inspirations'][0]['name'] == 'Patagonia'
    
    # Step 3: Use in PromptCompiler
    profile_defaults = ProfileDefaults(
        company=profile['company'],
        industry=profile['industry'],
        signature_tone=profile['tone'],
        platforms=profile['platforms'],
        brand_inspirations=profile['brand_inspirations'],
        brand_anti_inspirations=profile['brand_anti_inspirations']
    )
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    
    run_toggles = RunToggles(
        session_length=7,
        platform_focus=['instagram'],
        keywords=['eco-friendly', 'sustainable']
    )
    
    output = compiler.compile_for_social(run_toggles)
    
    # Step 4: Verify inspiration is applied
    assert output['model_context']['inspiration_applied'] is True
    
    inspiration_style = output['model_context']['inspiration_style']
    assert inspiration_style is not None
    assert len(inspiration_style['descriptors']) > 0
    
    # Should have extracted "authentic" from Patagonia
    descriptors_str = ' '.join(inspiration_style['descriptors']).lower()
    assert 'authentic' in descriptors_str or 'simple' in descriptors_str
    
    # Should have anti-pattern from "salesy"
    dont_str = ' '.join(inspiration_style['dont']).lower()
    assert 'sales' in dont_str or 'aggressive' in dont_str
    
    # Step 5: Verify safety constraint in prompt
    system_prompt = output['prompt_set']['system']
    assert 'Do not imitate' in system_prompt or 'do not reproduce' in system_prompt.lower()
    
    # Step 6: Verify context includes inspiration
    context = output['prompt_set']['context']
    assert 'inspiration' in context.lower() or 'authentic' in context.lower()


def test_vibe_preset_full_workflow(client):
    """Test complete workflow with vibe preset instead of brands."""
    
    # Save vibe preset
    response = client.post('/api/profile', json={
        'company': 'Health Clinic',
        'industry': 'healthcare',
        'tone': 'professional',
        'vibe_preset': 'clinical_trustworthy'
    })
    
    assert response.status_code == 200
    
    # Retrieve and verify
    response = client.get('/api/profile')
    profile = response.get_json()['profile']
    
    assert profile['vibe_preset'] == 'clinical_trustworthy'
    
    # Use in compiler
    profile_defaults = ProfileDefaults(
        company=profile['company'],
        industry=profile['industry'],
        vibe_preset=profile['vibe_preset']
    )
    
    compiler = PromptCompiler(profile_defaults=profile_defaults)
    output = compiler.compile_for_social(RunToggles(session_length=7))
    
    # Verify vibe preset applied
    assert output['model_context']['inspiration_applied'] is True
    inspiration_style = output['model_context']['inspiration_style']
    
    descriptors_str = ' '.join(inspiration_style['descriptors']).lower()
    assert 'professional' in descriptors_str or 'trustworthy' in descriptors_str


def test_combined_with_voice_fingerprint(client):
    """Test that inspiration works alongside voice fingerprint."""
    
    # Save both inspiration and voice profile
    voice_profile = {
        'sentence_length_band': 'short',
        'emoji_rate': 'none',
        'top_phrases': ['amazing', 'grateful', 'community'],
        'signature_moves': ['direct statements']
    }
    
    response = client.post('/api/profile', json={
        'company': 'Yoga Studio',
        'industry': 'fitness',
        'tone': 'warm',
        'brand_inspirations': [
            {'name': 'Lululemon', 'why': 'inspiring and wellness-focused'}
        ],
        'voice_profile': voice_profile
    })
    
    assert response.status_code == 200
    
    # Retrieve
    response = client.get('/api/profile')
    profile = response.get_json()['profile']
    
    # Use in compiler with both
    from services.generation.prompt_compiler import VoiceFingerprint
    
    profile_defaults = ProfileDefaults(
        company=profile['company'],
        brand_inspirations=profile['brand_inspirations']
    )
    
    voice_fp = VoiceFingerprint(
        sentence_length_band='short',
        emoji_rate='none',
        top_phrases=['amazing', 'grateful'],
        avoid_phrases=[],
        signature_moves=['direct']
    )
    
    compiler = PromptCompiler(
        profile_defaults=profile_defaults,
        voice_fingerprint=voice_fp
    )
    
    output = compiler.compile_for_social(RunToggles(session_length=7))
    
    # Both should be applied
    assert output['model_context']['inspiration_applied'] is True
    assert output['model_context']['voice_applied'] is True
    
    # Voice should come after inspiration in context (higher priority)
    context = output['prompt_set']['context']
    inspiration_pos = context.find('BRAND INSPIRATION')
    voice_pos = context.find('VOICE STYLE')
    
    if inspiration_pos >= 0 and voice_pos >= 0:
        assert voice_pos > inspiration_pos, "Voice should appear after inspiration"
