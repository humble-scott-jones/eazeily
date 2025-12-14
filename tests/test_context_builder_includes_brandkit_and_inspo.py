"""Tests for context_builder Brand Kit and Brand Inspiration integration."""

import pytest
from services.generation.context_builder import (
    merge_contexts,
    evaluate_brand_kit_tier,
    extract_brand_kit_from_user_data,
    format_brand_kit_bullets
)
from services.generation.output_schemas import BrandKitV1


def test_merge_contexts_includes_brand_kit():
    """Test that merge_contexts properly includes brand_kit in workspace context."""
    brand_kit: BrandKitV1 = {
        'services': ['SEO consulting', 'Content strategy'],
        'audience_role': 'Small business owners',
        'audience_pain': 'Struggling to rank on Google',
        'audience_outcome': 'More organic traffic',
        'differentiators': ['10+ years experience', 'Custom strategies'],
        'proof': ['50+ successful campaigns', 'Featured in Forbes']
    }
    
    workspace = {
        'company_name': 'Growth Co',
        'industry': 'marketing'
    }
    
    context = merge_contexts(
        workspace=workspace,
        brand_kit=brand_kit
    )
    
    # Check brand_kit is in workspace context
    assert context['workspace']['brand_kit'] is not None
    assert context['workspace']['brand_kit']['services'] == ['SEO consulting', 'Content strategy']
    assert context['workspace']['brand_kit']['audience_role'] == 'Small business owners'
    
    # Check tier is evaluated
    assert context['workspace']['brand_kit_tier'] == 'best'


def test_merge_contexts_with_brand_inspiration():
    """Test that brand_inspiration works alongside brand_kit."""
    brand_kit: BrandKitV1 = {
        'services': ['Coaching'],
        'audience_role': 'Executives'
    }
    
    voice_guide = {
        'tone_descriptors': ['confident', 'direct'],
        'sentence_length': 'short'
    }
    
    context = merge_contexts(
        brand_kit=brand_kit,
        voice_guide=voice_guide
    )
    
    # Both should be present
    assert context['workspace']['brand_kit'] is not None
    assert context['voice_guide'] is not None
    assert context['voice_guide']['tone_descriptors'] == ['confident', 'direct']


def test_evaluate_brand_kit_tier_best():
    """Test tier evaluation: best tier."""
    brand_kit: BrandKitV1 = {
        'services': ['Web design'],
        'audience_role': 'Startups',
        'audience_pain': 'Need professional website',
        'proof': ['100+ sites built']
    }
    
    tier = evaluate_brand_kit_tier(brand_kit)
    assert tier == 'best'


def test_evaluate_brand_kit_tier_stronger():
    """Test tier evaluation: stronger tier."""
    brand_kit: BrandKitV1 = {
        'services': ['Consulting'],
        'audience_role': 'Business owners',
        'audience_pain': 'Lack of clarity'
    }
    
    tier = evaluate_brand_kit_tier(brand_kit)
    assert tier == 'stronger'


def test_evaluate_brand_kit_tier_minimum():
    """Test tier evaluation: minimum tier."""
    brand_kit: BrandKitV1 = {
        'services': ['Training']
    }
    
    tier = evaluate_brand_kit_tier(brand_kit)
    assert tier == 'minimum'


def test_evaluate_brand_kit_tier_incomplete():
    """Test tier evaluation: incomplete (no services)."""
    brand_kit: BrandKitV1 = {
        'audience_role': 'Entrepreneurs'
    }
    
    tier = evaluate_brand_kit_tier(brand_kit)
    assert tier == 'incomplete'


def test_extract_brand_kit_from_user_data_structured():
    """Test extracting brand_kit when it's already structured."""
    user_data = {
        'brand_kit': {
            'services': ['Design', 'Development'],
            'audience_role': 'Tech startups',
            'proof': ['10 years', '50+ clients']
        }
    }
    
    brand_kit = extract_brand_kit_from_user_data(user_data)
    
    assert brand_kit is not None
    assert brand_kit['services'] == ['Design', 'Development']
    assert brand_kit['audience_role'] == 'Tech startups'


def test_extract_brand_kit_from_user_data_individual_fields():
    """Test extracting brand_kit from individual fields (backward compatibility)."""
    user_data = {
        'services': '["Coaching", "Consulting"]',
        'audience_role': 'Executives',
        'audience_pain': 'Time management issues',
        'differentiators': '["20 years experience", "Harvard MBA"]'
    }
    
    brand_kit = extract_brand_kit_from_user_data(user_data)
    
    assert brand_kit is not None
    assert brand_kit['services'] == ['Coaching', 'Consulting']
    assert brand_kit['audience_role'] == 'Executives'
    assert brand_kit['audience_pain'] == 'Time management issues'
    assert brand_kit['differentiators'] == ['20 years experience', 'Harvard MBA']


def test_extract_brand_kit_from_user_data_csv_format():
    """Test extracting brand_kit from CSV format strings."""
    user_data = {
        'services': 'Design, Development, Branding',
        'proof': 'Award winner, Featured in TechCrunch'
    }
    
    brand_kit = extract_brand_kit_from_user_data(user_data)
    
    assert brand_kit is not None
    assert brand_kit['services'] == ['Design', 'Development', 'Branding']
    assert brand_kit['proof'] == ['Award winner', 'Featured in TechCrunch']


def test_extract_brand_kit_from_user_data_empty():
    """Test extracting brand_kit when no data exists."""
    user_data = {
        'company': 'Test Co',
        'industry': 'tech'
    }
    
    brand_kit = extract_brand_kit_from_user_data(user_data)
    
    assert brand_kit is None


def test_format_brand_kit_bullets():
    """Test formatting brand_kit as bullet-point sections."""
    brand_kit: BrandKitV1 = {
        'services': ['Web design', 'SEO', 'Content writing'],
        'audience_role': 'Small businesses',
        'audience_pain': 'Low online visibility',
        'audience_outcome': 'More customers',
        'audience_objection': 'Too expensive',
        'differentiators': ['Affordable pricing', 'Fast turnaround'],
        'proof': ['50+ happy clients', 'Featured in Forbes']
    }
    
    sections = format_brand_kit_bullets(brand_kit)
    
    # Check business summary
    assert 'Web design' in sections['business_summary']
    assert 'Small businesses' in sections['business_summary']
    
    # Check services bullets
    assert '• Web design' in sections['services_bullets']
    assert '• SEO' in sections['services_bullets']
    
    # Check audience bullets
    assert '• Who: Small businesses' in sections['audience_bullets']
    assert '• Pain: Low online visibility' in sections['audience_bullets']
    assert '• Outcome: More customers' in sections['audience_bullets']
    assert '• Objection: Too expensive' in sections['audience_bullets']
    
    # Check proof bullets
    assert '• 50+ happy clients' in sections['proof_bullets']
    assert '• Featured in Forbes' in sections['proof_bullets']
    
    # Check differentiators bullets
    assert '• Affordable pricing' in sections['differentiators_bullets']
    assert '• Fast turnaround' in sections['differentiators_bullets']


def test_format_brand_kit_bullets_minimal():
    """Test formatting brand_kit with minimal data."""
    brand_kit: BrandKitV1 = {
        'services': ['Coaching']
    }
    
    sections = format_brand_kit_bullets(brand_kit)
    
    # Should have services
    assert '• Coaching' in sections['services_bullets']
    
    # Empty sections should be empty strings
    assert sections['audience_bullets'] == ''
    assert sections['proof_bullets'] == ''
    assert sections['differentiators_bullets'] == ''


def test_merge_contexts_without_brand_kit():
    """Test that merge_contexts works without brand_kit (backward compatibility)."""
    workspace = {
        'company_name': 'Test Co',
        'industry': 'tech'
    }
    
    context = merge_contexts(workspace=workspace)
    
    # Should work fine
    assert context is not None
    assert context['workspace']['company_name'] == 'Test Co'
    assert context['workspace'].get('brand_kit') is None
    assert context['workspace'].get('brand_kit_tier') is None


def test_brand_kit_tier_with_differentiators_only():
    """Test tier evaluation with differentiators but no proof."""
    brand_kit: BrandKitV1 = {
        'services': ['Consulting'],
        'audience_role': 'CEOs',
        'differentiators': ['30 years experience']
    }
    
    tier = evaluate_brand_kit_tier(brand_kit)
    assert tier == 'best'  # Has services + audience + differentiators


def test_brand_kit_tier_with_outcome_but_no_role():
    """Test tier evaluation with audience outcome but no role."""
    brand_kit: BrandKitV1 = {
        'services': ['Training'],
        'audience_outcome': 'Better productivity'
    }
    
    tier = evaluate_brand_kit_tier(brand_kit)
    assert tier == 'stronger'  # Has services + audience (outcome counts)
