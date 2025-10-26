import json
import sqlite3
import uuid
import types
import generator as gen_mod
import app as togetherly_app


def test_generate_includes_goals_and_keywords(client, monkeypatch, tmp_path):
    # Create a user in the temp DB and set session
    user_id = str(uuid.uuid4())
    db_path = togetherly_app.DB_PATH  # set by conftest
    con = sqlite3.connect(db_path)
    con.execute(
        "INSERT INTO users (id, email, password_hash, is_paid, free_sample_used) VALUES (?, ?, ?, ?, ?)",
        (user_id, 'test@example.com', 'hash', 0, 0),
    )
    con.commit()
    con.close()

    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['profile_id'] = str(uuid.uuid4())

    # Capture args passed to generator.generate_posts
    calls = {}

    def fake_generate_posts(*, days, start_day, industry, tone, platforms, brand_keywords, include_images, niche_keywords, goals, details, company):
        calls['kwargs'] = dict(
            days=days,
            industry=industry,
            tone=tone,
            platforms=list(platforms),
            brand_keywords=list(brand_keywords),
            niche_keywords=list(niche_keywords),
            goals=list(goals),
            details=dict(details or {}),
            include_images=bool(include_images),
            company=company,
        )
        # Return a simple valid payload
        return [
            {
                'date': start_day.isoformat(),
                'day_index': 1,
                'platform': platforms[0],
                'pillar': 'Story',
                'caption': 'Hello world',
                'image_prompt': 'A friendly scene',
                'image_url': None,
                'reel': None,
            }
        ]

    monkeypatch.setattr(gen_mod, 'generate_posts', fake_generate_posts)

    payload = {
        'days': 1,
        'industry': 'Bakery',
        'tone': 'friendly',
        'platforms': ['instagram'],
        'brand_keywords': ['artisan', 'sourdough'],
        'niche_keywords': ['local'],
        'goals': ['Drive sales', 'Engagement'],
        'details': {'reel_style': 'Face-camera tips'},
        'company': "Laura's Bakery",
        'include_images': False,
    }

    r = client.post('/api/generate', json=payload)
    assert r.status_code == 200
    out = r.get_json()
    assert out['count'] == 1
    # Assert the generator received the intended shaping fields
    assert 'kwargs' in calls
    seen = calls['kwargs']
    assert seen['brand_keywords'] == payload['brand_keywords']
    assert seen['niche_keywords'] == payload['niche_keywords']
    assert seen['goals'] == payload['goals']
    assert seen['tone'] == 'friendly'
    assert seen['platforms'] == ['instagram']
