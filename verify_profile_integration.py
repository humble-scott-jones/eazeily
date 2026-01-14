#!/usr/bin/env python3
"""
Manual verification script for profile integration fix.

This script demonstrates that profile data correctly flows through
the content generation pipeline.

Usage:
    python3 verify_profile_integration.py
"""

def main():
    print("=" * 70)
    print("PROFILE INTEGRATION VERIFICATION")
    print("=" * 70)
    print()
    
    # Step 1: Verify dummy profile
    print("Step 1: Verifying dummy profile has all required methods...")
    from routes.generate_routes import _build_dummy_profile
    
    dummy = _build_dummy_profile()
    required_methods = [
        'get_writing_samples',
        'get_brand_keywords',
        'get_niche_keywords',
        'get_customers',
        'get_scraped_meta',
        'get_defaults',
        'get_examples'
    ]
    
    all_present = True
    for method in required_methods:
        has_method = hasattr(dummy, method) and callable(getattr(dummy, method))
        status = "✓" if has_method else "✗ MISSING"
        print(f"  {method:30} {status}")
        if not has_method:
            all_present = False
    
    if not all_present:
        print("\n❌ FAILED: Dummy profile is missing required methods")
        return False
    
    print("  ✓ All methods present")
    print()
    
    # Step 2: Verify VoiceEngine can use dummy profile
    print("Step 2: Verifying VoiceEngine works with dummy profile...")
    from services.voice_engine import VoiceEngine
    
    engine = VoiceEngine()
    try:
        result = engine.generate_expert_content(
            dummy,
            'Test topic',
            'post',
            'linkedin'
        )
        print(f"  ✓ Generated content: {len(result)} characters")
    except AttributeError as e:
        print(f"  ❌ FAILED: AttributeError - {e}")
        return False
    print()
    
    # Step 3: Verify profile data extraction
    print("Step 3: Verifying profile data flows into prompts...")
    
    class MockProfile:
        industry = 'Technology'
        business_name = 'TechCorp Inc'
        brand_voice = 'Innovative and professional'
        target_audience = 'Tech executives and CTOs'
        key_offer = 'AI-powered automation solutions'
        voice_rules = 'Always mention ROI, avoid technical jargon'
        
        def get_writing_samples(self):
            return ['We help Fortune 500 companies reduce costs by 40%.']
        
        def get_brand_keywords(self):
            return ['AI', 'automation', 'efficiency']
        
        def get_niche_keywords(self):
            return ['machine learning', 'cloud computing']
        
        def get_customers(self):
            return ['Enterprise', 'Fortune 500']
        
        def get_scraped_meta(self):
            return {'key_customers': 'Tech companies'}
    
    from unittest.mock import Mock
    
    mock_profile = MockProfile()
    mock_model = Mock()
    mock_response = Mock()
    mock_response.text = 'Generated content'
    
    captured_prompts = []
    
    def capture_prompt(prompt):
        captured_prompts.append(prompt)
        return mock_response
    
    mock_model.generate_content = capture_prompt
    engine.model = mock_model
    
    result = engine.generate_expert_content(
        mock_profile,
        'How AI is transforming business',
        'post',
        'linkedin'
    )
    
    if not captured_prompts:
        print("  ❌ FAILED: No prompt was captured")
        return False
    
    prompt = captured_prompts[0]
    
    # Check that all profile data is in the prompt
    checks = [
        ('Business name', 'TechCorp Inc', 'TechCorp' in prompt),
        ('Industry', 'Technology', 'Technology' in prompt),
        ('Brand voice', 'Innovative and professional', 'Innovative' in prompt or 'professional' in prompt),
        ('Target audience', 'Tech executives', 'Tech executives' in prompt or 'CTOs' in prompt),
        ('Key offer', 'AI-powered automation', 'AI-powered' in prompt or 'automation solutions' in prompt),
        ('Voice rules', 'ROI, no jargon', 'ROI' in prompt or 'jargon' in prompt),
        ('Brand keywords', 'AI, automation', 'AI' in prompt or 'automation' in prompt),
        ('Niche keywords', 'machine learning', 'machine learning' in prompt or 'cloud computing' in prompt),
        ('Customers', 'Enterprise, Fortune 500', 'Enterprise' in prompt or 'Fortune 500' in prompt),
        ('Writing samples', 'reduce costs by 40%', 'reduce costs' in prompt or 'Fortune 500 companies' in prompt)
    ]
    
    all_passed = True
    for field_name, value, check in checks:
        status = "✓" if check else "✗ MISSING"
        print(f"  {field_name:20} {status}")
        if not check:
            all_passed = False
            print(f"    Expected to find: {value}")
    
    if not all_passed:
        print("\n❌ FAILED: Some profile data missing from prompt")
        print("\nGenerated prompt preview:")
        print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        return False
    
    print()
    print("=" * 70)
    print("✅ ALL VERIFICATION CHECKS PASSED")
    print("=" * 70)
    print()
    print("Summary:")
    print("  • Dummy profile has all required methods")
    print("  • VoiceEngine works with dummy profile")
    print("  • Profile data flows correctly into generation prompts")
    print("  • All brand context, keywords, and voice rules are included")
    print()
    print("The profile integration fix is working correctly!")
    
    return True


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
