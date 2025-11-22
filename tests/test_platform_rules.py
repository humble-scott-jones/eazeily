from platform_rules import apply_platform_rules, DEFAULT_VARIANT_PLATFORMS


def test_rule_enforcement_truncates_long_copy():
    body = "This is an intentionally long line of copy " * 20
    payload = apply_platform_rules(
        body=body,
        platform='twitter',
        hashtags=[f"tag{i}" for i in range(6)],
        pillar_name='Story',
        goals=['engagement'],
        company='Test Co'
    )

    assert len(payload['text']) <= 260
    assert any('Trimmed copy' in note for note in payload['warnings'])
    assert len(payload['hashtags']) <= 3


def test_instagram_hashtag_limit_snapshot():
    body = "Concise caption with plenty of detail for the platform"
    payload = apply_platform_rules(
        body=body,
        platform='instagram',
        hashtags=[f"custom{i}" for i in range(20)],
        pillar_name='Engagement',
        goals=['comments']
    )

    assert payload['hashtags'] == [f"#custom{i}" for i in range(12)]
    assert 'Trimmed hashtags' in ' '.join(payload.get('warnings', []))


def test_default_platform_list_exposes_all_targets():
    assert 'twitter' in DEFAULT_VARIANT_PLATFORMS
    assert 'youtube' in DEFAULT_VARIANT_PLATFORMS
