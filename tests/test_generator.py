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
    
    # Each post should have variants for all supported platforms
    for post in posts:
        assert 'variants' in post
        assert post['variants'] is not None
        assert 'instagram' in post['variants']
        assert 'facebook' in post['variants']
        assert 'linkedin' in post['variants']
        assert 'twitter' in post['variants']
        assert 'youtube' in post['variants']
        insta_variant = post['variants']['instagram']
        assert isinstance(insta_variant, dict)
        assert len(insta_variant.get('text', '')) > 0

def test_generate_posts_single_platform_includes_variants():
    """Even single-platform plans should include cross-platform variants"""
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
    
    # Variants should still be present for downstream UI
    assert isinstance(posts[0].get('variants'), dict)
    assert 'instagram' in posts[0]['variants']
