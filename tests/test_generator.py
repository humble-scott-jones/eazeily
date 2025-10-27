from generator import make_caption, generate_posts
from datetime import date

def test_make_caption_includes_company():
    caption = make_caption(
        industry='Bakery',
        tone='friendly',
        pillar_name='Product/Offer',
        pillar_hint='Highlight one offering',
        platform='instagram',
        brand_keywords=['artisan'],
        hashtags=['#bakery'],
        goals=['promote'],
        company='Laura\'s Bakery'
    )
    assert 'From Laura\'s Bakery.' in caption or 'From Laura\'s Bakery' in caption

def test_generate_posts_with_variants():
    """Test that posts include variants when multiple platforms are selected"""
    posts = generate_posts(
        days=1,
        start_day=date(2025, 1, 1),
        industry='Bakery',
        tone='friendly',
        platforms=['instagram', 'facebook', 'linkedin'],
        brand_keywords=['artisan'],
        include_images=False,
        niche_keywords=['bakery'],
        goals=['promote'],
        company='Test Bakery'
    )
    
    # Should have 3 posts (one per platform)
    assert len(posts) == 3
    
    # Each post should have variants
    for post in posts:
        assert 'variants' in post
        assert post['variants'] is not None
        assert len(post['variants']) == 3
        assert 'instagram' in post['variants']
        assert 'facebook' in post['variants']
        assert 'linkedin' in post['variants']
        # Each variant should be a string with content
        assert isinstance(post['variants']['instagram'], str)
        assert len(post['variants']['instagram']) > 0

def test_generate_posts_single_platform_no_variants():
    """Test that posts don't include variants for single platform"""
    posts = generate_posts(
        days=1,
        start_day=date(2025, 1, 1),
        industry='Bakery',
        tone='friendly',
        platforms=['instagram'],
        brand_keywords=['artisan'],
        include_images=False,
        niche_keywords=['bakery'],
        goals=['promote'],
        company='Test Bakery'
    )
    
    # Should have 1 post
    assert len(posts) == 1
    
    # Should not have variants (or variants is None) for single platform
    assert posts[0].get('variants') is None
