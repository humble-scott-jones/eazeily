import pytest
from generator import default_hashtags, make_reel_plan


def test_default_hashtags_basic():
    tags = default_hashtags('Bakery', ['sourdough', 'artisan'])
    assert isinstance(tags, list)
    assert any(t.lower().startswith('#bakery') for t in tags)
    assert any('#sourdough' in t.lower() for t in tags)


def test_make_reel_plan_structure():
    plan = make_reel_plan('bakery', 'Pillar', ['brand'], 'friendly', company='Co', reel_style='Face-camera tips', length_seconds=30)
    assert isinstance(plan, dict)
    assert plan.get('length_seconds') == 30
    assert 'beats' in plan and isinstance(plan['beats'], list) and len(plan['beats']) >= 1
    assert 'srt' in plan and isinstance(plan['srt'], str) and len(plan['srt']) > 0
    assert 'thumbnail_prompt' in plan
    assert plan.get('caption_overlays') and all(len(item['text']) <= item['safe_chars'] for item in plan['caption_overlays'])
    assert plan.get('first_frame_idea')
    assert plan.get('engagement_prompts')
    assert plan.get('posting_checklist')
    assert plan.get('looping_hint')


def test_reel_plan_platform_and_variant_metadata():
    light_plan = make_reel_plan(
        'bakery', 'Pillar', ['brand'], 'friendly', company='Co', reel_style='Face-camera tips', length_seconds=20, production_tier='solo'
    )
    upgraded_plan = make_reel_plan(
        'bakery', 'Pillar', ['brand'], 'friendly', company='Co', reel_style='Face-camera tips', length_seconds=20, production_tier='studio'
    )

    assert light_plan.get('variant') == 'resource_light'
    assert upgraded_plan.get('variant') == 'upgraded'

    specs = light_plan.get('platform_specs') or []
    assert any(s.get('platform') == 'instagram' for s in specs)
    assert 'csv' in (light_plan.get('shoot_list_exports') or {})

    overlays = light_plan.get('caption_overlays') or []
    assert overlays and all(len(item.get('text', '')) <= item.get('safe_chars', 0) for item in overlays)
    assert light_plan.get('first_frame_idea') and light_plan.get('looping_hint')
    assert light_plan.get('engagement_prompts') and light_plan.get('posting_checklist')
