#!/usr/bin/env python3
"""Manual test script for profile update functionality."""

import sys
import os

# Add the repo to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.conversation_router import ConversationRouter

class MockProfile:
    """Mock VoiceProfile for testing."""
    def __init__(self):
        self.business_name = 'Test Bakery'
        self.industry = 'Food & Beverage'
        self.brand_voice = 'warm and friendly'
        self.target_audience = 'busy parents'

def test_profile_commands():
    """Test profile command parsing."""
    router = ConversationRouter()
    profile = MockProfile()
    
    print("=" * 60)
    print("TESTING PROFILE UPDATE COMMANDS")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        ("/profile", "View profile"),
        ("/update", "Generic update"),
        ("/voice", "Update voice shortcut"),
        ("/audience", "Update audience shortcut"),
        ("show me my profile", "Natural language view"),
        ("change my brand voice to professional", "Natural language voice update"),
        ("update my target audience to millennials", "Natural language audience update"),
        ("I want to update my profile", "Generic update intent"),
    ]
    
    for message, description in test_cases:
        print(f"\n{description}:")
        print(f"  Input: '{message}'")
        result = router.parse_intent(message, profile)
        print(f"  Task Type: {result.get('task_type')}")
        print(f"  Follow-up Needed: {result.get('follow_up_needed')}")
        if result.get('extracted_params'):
            print(f"  Extracted: {result.get('extracted_params')}")
        if result.get('follow_up_question'):
            print(f"  Question: {result.get('follow_up_question')[:80]}...")
    
    print("\n" + "=" * 60)
    print("TESTING FIELD NAME NORMALIZATION")
    print("=" * 60)
    
    field_tests = [
        "voice",
        "tone",
        "brand voice",
        "audience",
        "target audience",
        "customers",
        "business name",
        "company",
        "industry",
        "offer",
        "value prop",
    ]
    
    for field_input in field_tests:
        normalized = router.normalize_field_name(field_input)
        print(f"  '{field_input}' → {normalized}")
    
    print("\n" + "=" * 60)
    print("✅ Manual testing complete!")
    print("=" * 60)

if __name__ == '__main__':
    test_profile_commands()
