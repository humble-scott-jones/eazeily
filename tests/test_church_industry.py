"""
Test Church industry configuration and functionality.
"""
import json
import os
from generator import generate_posts, default_hashtags
from datetime import date


def test_church_industry_in_config():
    """Verify Church industry exists in config.json with all required fields."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'content', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    industries = config.get('industries', [])
    church = next((ind for ind in industries if ind.get('key') == 'church'), None)
    
    assert church is not None, "Church industry not found in config.json"
    assert church.get('label') == 'Church', f"Expected label 'Church', got {church.get('label')}"
    assert church.get('icon') == '⛪', f"Expected icon '⛪', got {church.get('icon')}"
    assert 'suggested_keywords' in church, "Church industry missing suggested_keywords"
    assert len(church.get('suggested_keywords', [])) > 0, "Church industry has no suggested keywords"
    assert 'note_placeholder' in church, "Church industry missing note_placeholder"
    
    # Verify suggested keywords include church-relevant terms
    keywords = church.get('suggested_keywords', [])
    church_related = ['Sunday service', 'community', 'sermon', 'worship', 'volunteer']
    # At least some church-related keywords should be present (case-insensitive check)
    keywords_lower = [k.lower() for k in keywords]
    assert any(term.lower() in keywords_lower for term in church_related), \
        f"Expected church-related keywords in {keywords}"


def test_church_industry_questions():
    """Verify Church industry has appropriate questions defined."""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'content', 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    questions = config.get('questions', {})
    church_questions = questions.get('church')
    
    assert church_questions is not None, "Church questions not found in config.json"
    assert len(church_questions) > 0, "Church has no questions defined"
    
    # Verify structure of questions
    for q in church_questions:
        assert 'type' in q, f"Question missing 'type': {q}"
        assert 'key' in q, f"Question missing 'key': {q}"
        assert 'label' in q, f"Question missing 'label': {q}"
        
        if q['type'] == 'chips':
            assert 'options' in q, f"Chips question missing 'options': {q}"
            assert len(q['options']) > 0, f"Chips question has no options: {q}"


def test_church_post_generation():
    """Test that posts can be generated for Church industry."""
    posts = generate_posts(
        days=3,
        start_day=date.today(),
        industry='Church',
        tone='inspirational',
        platforms=['instagram', 'facebook'],
        brand_keywords=['community', 'worship'],
        include_images=True,
        niche_keywords=['Sunday service', 'sermon'],
        goals=['Sermons', 'Community'],
        company='Grace Community Church'
    )
    
    assert len(posts) > 0, "No posts generated for Church industry"
    assert len(posts) == 6, f"Expected 6 posts (3 days × 2 platforms), got {len(posts)}"
    
    # Verify post content
    for post in posts:
        assert 'caption' in post, "Post missing caption"
        assert 'platform' in post, "Post missing platform"
        assert 'pillar' in post, "Post missing pillar"
        
        # Check that caption includes relevant content
        caption = post['caption'].lower()
        assert 'church' in caption or 'grace community church' in caption, \
            f"Caption doesn't mention church: {post['caption']}"


def test_church_hashtags():
    """Test that Church-specific hashtags are generated appropriately."""
    hashtags = default_hashtags('Church', ['Sunday service', 'sermon', 'worship'])
    
    assert len(hashtags) > 0, "No hashtags generated for Church"
    
    # Check for relevant hashtags (they should be lowercased and combined)
    hashtags_str = ' '.join(hashtags).lower()
    assert '#church' in hashtags_str or 'church' in hashtags_str.replace('#', ''), \
        f"Expected Church-related hashtags, got {hashtags}"


def test_church_inspirational_tone():
    """Verify that Church industry works well with inspirational tone."""
    posts = generate_posts(
        days=1,
        start_day=date.today(),
        industry='Church',
        tone='inspirational',
        platforms=['facebook'],
        brand_keywords=['faith', 'community'],
        include_images=False,
        niche_keywords=['worship'],
        goals=['Community'],
        company='Faith Church'
    )
    
    assert len(posts) == 1, f"Expected 1 post, got {len(posts)}"
    post = posts[0]
    
    # Verify tone guidance is in the caption
    caption = post['caption']
    assert 'inspirational' in caption.lower() or 'uplifting' in caption.lower(), \
        f"Expected inspirational tone in caption: {caption}"
