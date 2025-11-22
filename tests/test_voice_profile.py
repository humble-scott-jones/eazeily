import voice_profile


def test_profile_from_samples_builds_embedding():
    samples = [
        "We love celebrating small wins with our crew.",
        "Friendly reminder: book your session early and bring questions!",
        "We keep posts punchy, helpful, and always invite replies.",
        "Your ideas drive our roadmap—drop them below.",
        "Morning cadence, warm tone, and plenty of encouragement."
    ]
    profile = voice_profile.profile_from_samples(samples)
    assert profile['sample_count'] == len(samples)
    assert 'embedding' in profile and profile['embedding']
    assert 'include_phrases' in profile and profile['include_phrases']
    assert profile['avg_length'] > 4


def test_assess_text_flags_drift_and_messages():
    samples = [
        "We keep it warm, helpful, and upbeat—always inviting the reader in.",
        "Remember: quick wins and friendly calls to action are our jam.",
        "Short, encouraging lines make our posts feel human."
    ]
    profile = voice_profile.profile_from_samples(samples)
    on_brand = "Quick win: share your first draft today—our team is cheering you on!"
    off_brand = "Quarterly EBITDA results have been reconciled per the new compliance memo."

    strong = voice_profile.assess_text(profile, on_brand, threshold=0.72)
    drift = voice_profile.assess_text(profile, off_brand, threshold=0.72)

    assert strong['score'] > drift['score']
    assert drift['drift'] is True
    assert drift['message']
    assert any('phrase' in s.lower() for s in drift.get('suggestions', []))


def test_evaluate_prompts_wraps_assessment():
    samples = [
        "We cheer on every customer milestone with short, kind notes.",
        "Keep it encouraging and specific—no stiff jargon.",
        "Punchy hooks, clear CTAs, plenty of gratitude."
    ]
    profile = voice_profile.profile_from_samples(samples)
    prompts = [
        "New drop: tag us when you try it!",
        "This memorandum outlines our Q4 audit requirements."
    ]
    results = voice_profile.evaluate_prompts(profile, prompts, threshold=0.7)
    assert len(results) == 2
    assert results[1]['drift'] is True
