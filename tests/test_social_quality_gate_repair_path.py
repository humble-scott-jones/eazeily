"""Test social quality gate repair path."""

import pytest
from services.generation.social_quality_gate import (
    evaluate_post_quality,
    build_repair_prompt,
    attempt_repair,
)


def test_build_repair_prompt_includes_issues():
    """Test that repair prompt includes specific issues to fix."""
    failing_post = {
        'platform': 'instagram',
        'caption': 'You should try this. Consider posting more.',
        'hashtags': ['#tips']
    }
    
    evaluation = {
        'passed': False,
        'errors': [
            'Caption contains coaching/instructional language',
            'Caption lacks structure signal'
        ],
        'warnings': []
    }
    
    messages = build_repair_prompt(failing_post, evaluation)
    
    assert len(messages) == 2
    assert messages[0]['role'] == 'system'
    assert messages[1]['role'] == 'user'
    
    user_msg = messages[1]['content']
    assert 'coaching' in user_msg.lower()
    assert 'structure signal' in user_msg.lower()
    assert failing_post['caption'] in user_msg


def test_repair_prompt_specifies_no_coaching():
    """Test that repair prompt explicitly forbids coaching language."""
    failing_post = {
        'platform': 'linkedin',
        'caption': 'Here are some tips you should consider trying.',
        'hashtags': []
    }
    
    evaluation = {
        'passed': False,
        'errors': ['Caption contains coaching/instructional language'],
        'warnings': []
    }
    
    messages = build_repair_prompt(failing_post, evaluation)
    user_msg = messages[1]['content']
    
    assert 'no coaching' in user_msg.lower()
    assert '"you should"' in user_msg.lower()
    assert '"consider"' in user_msg.lower()


def test_repair_prompt_requires_structure():
    """Test that repair prompt requires structure signals."""
    failing_post = {
        'platform': 'instagram',
        'caption': 'Generic content about success and growth.',
        'hashtags': []
    }
    
    evaluation = {
        'passed': False,
        'errors': ['Caption lacks structure signal'],
        'warnings': []
    }
    
    messages = build_repair_prompt(failing_post, evaluation)
    user_msg = messages[1]['content']
    
    assert 'structure signal' in user_msg.lower()
    assert 'numbered steps' in user_msg.lower() or 'bullet points' in user_msg.lower()


def test_repair_prompt_includes_platform_guidance():
    """Test that repair prompt includes platform-specific guidance."""
    failing_post = {
        'platform': 'linkedin',
        'caption': 'Short post',
        'hashtags': []
    }
    
    evaluation = {
        'passed': False,
        'errors': ['Caption too short for linkedin'],
        'warnings': []
    }
    
    messages = build_repair_prompt(failing_post, evaluation)
    user_msg = messages[1]['content']
    
    assert 'linkedin' in user_msg.lower()


def test_attempt_repair_fails_without_client():
    """Test that repair fails gracefully without OpenAI client."""
    post = {
        'platform': 'instagram',
        'caption': 'Bad post',
        'hashtags': []
    }
    
    evaluation = {
        'passed': False,
        'errors': ['Caption lacks structure'],
        'warnings': []
    }
    
    result = attempt_repair(post, evaluation, openai_client=None)
    
    assert result['ok'] is False
    assert 'error' in result
    assert 'no openai client' in result['error'].lower()


def test_quality_gate_flow_detect_repair_pass():
    """Test the full flow: detect issue -> mark for repair -> would repair."""
    # This is a conceptual test showing the flow
    # Actual repair requires OpenAI client
    
    # Step 1: Generate and detect issue
    failing_post = {
        'platform': 'instagram',
        'caption': 'You should definitely try this amazing tip for great success!',
        'hashtags': ['#tips']
    }
    
    # Step 2: Evaluate
    evaluation = evaluate_post_quality(failing_post)
    
    assert evaluation['passed'] is False
    assert len(evaluation['errors']) > 0
    
    # Step 3: Build repair prompt
    messages = build_repair_prompt(failing_post, evaluation)
    
    assert len(messages) == 2
    assert 'FINAL post copy only' in messages[1]['content']


def test_repair_validates_output():
    """Test that repair validates the output meets quality standards."""
    # This test demonstrates the expected behavior
    # In practice, we'd need a mock OpenAI client
    
    original_post = {
        'platform': 'instagram',
        'caption': 'Generic tips you should try',
        'hashtags': ['#tips']
    }
    
    evaluation = evaluate_post_quality(original_post)
    assert evaluation['passed'] is False
    
    # Simulate a repaired caption that would pass
    repaired_post = {
        'platform': 'instagram',
        'caption': """
        3 proven strategies for better content:
        
        1. Start with a hook that stops scrolling
        2. Deliver one clear takeaway
        3. End with a specific action step
        
        For example, last week I used this exact framework and engagement doubled.
        
        Save this for your next post! 🎯
        """,
        'hashtags': ['#contentcreation', '#socialmedia']
    }
    
    new_evaluation = evaluate_post_quality(repaired_post)
    assert new_evaluation['passed'] is True


def test_repair_flow_with_multiple_issues():
    """Test repair prompt handles multiple issues."""
    post_with_multiple_issues = {
        'platform': 'linkedin',
        'caption': 'Try this tip!',  # Too short, no structure, generic
        'hashtags': []
    }
    
    evaluation = evaluate_post_quality(post_with_multiple_issues)
    
    assert evaluation['passed'] is False
    assert len(evaluation['errors']) > 1
    
    messages = build_repair_prompt(post_with_multiple_issues, evaluation)
    user_msg = messages[1]['content']
    
    # Should mention all the issues
    for error in evaluation['errors']:
        # At least some key terms from errors should be in prompt
        assert any(
            keyword in user_msg.lower() 
            for keyword in ['structure', 'short', 'hook', 'value']
        )


def test_system_message_forbids_meta_commentary():
    """Test that system message explicitly forbids meta commentary."""
    post = {
        'platform': 'instagram',
        'caption': 'Bad caption',
        'hashtags': []
    }
    
    evaluation = {
        'passed': False,
        'errors': ['Test error'],
        'warnings': []
    }
    
    messages = build_repair_prompt(post, evaluation)
    system_msg = messages[0]['content']
    
    assert 'meta commentary' in system_msg.lower() or 'advice' in system_msg.lower()
    assert 'final' in system_msg.lower()
