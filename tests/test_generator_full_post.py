from generator import make_full_post
import random


def test_make_full_post_includes_theme():
    random.seed(123)
    result = make_full_post(
        industry='Bakery',
        tone='friendly',
        pillar_name='Educational',
        pillar_hint='Share a quick tip that solves a common problem for your audience.',
        platform='instagram',
        brand_keywords=['artisan'],
        hashtags=['#bakery', '#bread'],
        goals=['engagement'],
        company='Test Bakery',
        theme='sourdough'
    )
    caption = result.get('caption', '').lower()
    assert 'sourdough' in caption
    # should have at least two mentions of theme
    assert caption.count('sourdough') >= 1
    assert '#' in caption


def test_make_full_post_without_theme_returns_caption():
    random.seed(42)
    result = make_full_post(
        industry='Bakery',
        tone='friendly',
        pillar_name='Educational',
        pillar_hint='Share a quick tip',
        platform='instagram',
        brand_keywords=['artisan'],
        hashtags=['#bakery'],
        goals=[],
        company=''
    )
    assert isinstance(result, dict)
    assert 'caption' in result
    assert result['theme'] is None
