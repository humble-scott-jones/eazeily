import json
import sqlite3
import uuid

import app as appmod


def _fetch_feedback_rows(db_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    rows = con.execute('SELECT rating, post_day, platform, note FROM feedback').fetchall()
    con.close()
    return rows


def _seed_user_with_profile(db_path, email='feedback@example.com'):
    user_id = f'user-{uuid.uuid4().hex[:8]}'
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.execute(
        'INSERT INTO users (id, email, password_hash, is_paid, free_sample_used) VALUES (?, ?, ?, 0, 0)',
        (user_id, email.lower(), 'hash')
    )
    con.execute(
        'INSERT INTO profiles (id, industry, tone, platforms, brand_keywords, niche_keywords, goals, company, include_images, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)',
        (
            user_id,
            'retail',
            'friendly',
            json.dumps(['instagram']),
            json.dumps(['artisan']),
            json.dumps([]),
            json.dumps([]),
            'Demo Co',
            json.dumps({})
        )
    )
    con.commit()
    con.close()
    return user_id


def test_feedback_endpoint_persists_note(client):
    with client.session_transaction() as sess:
        sess['profile_id'] = 'profile-note'
    resp = client.post('/api/feedback', json={
        'rating': -1,
        'post_day': 3,
        'platform': 'instagram',
        'note': 'Too generic for our brand'
    })
    assert resp.status_code == 200
    rows = _fetch_feedback_rows(client.application.DB_PATH)  # type: ignore[attr-defined]
    assert len(rows) == 1
    row = rows[0]
    assert row['rating'] == -1
    assert row['note'] == 'Too generic for our brand'


def test_feedback_note_truncated_to_limit(client):
    with client.session_transaction() as sess:
        sess['profile_id'] = 'profile-long'
    long_note = 'x' * (appmod.MAX_FEEDBACK_NOTE_LEN + 50)
    resp = client.post('/api/feedback', json={
        'rating': -1,
        'post_day': 1,
        'platform': 'facebook',
        'note': long_note
    })
    assert resp.status_code == 200
    rows = _fetch_feedback_rows(client.application.DB_PATH)  # type: ignore[attr-defined]
    assert len(rows) == 1
    assert len(rows[0]['note']) == appmod.MAX_FEEDBACK_NOTE_LEN


def test_feedback_report_requires_auth(client):
    resp = client.post('/api/feedback/report', json={'summary': 'Need multi image', 'details': 'Please allow carousels'})
    assert resp.status_code == 401


def test_feedback_report_persists_issue(client):
    user_id = _seed_user_with_profile(client.application.DB_PATH)  # type: ignore[attr-defined]
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['profile_id'] = user_id
    payload = {
        'summary': 'Need better scheduling',
        'details': 'Let me pick dates for each generated post.',
        'category': 'idea',
        'allow_contact': True,
        'platform': 'instagram',
        'plan_length': 7
    }
    resp = client.post('/api/feedback/report', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['ok'] is True
    rows = _fetch_feedback_rows(client.application.DB_PATH)  # type: ignore[attr-defined]
    assert len(rows) == 1
    row = rows[0]
    assert row['platform'] == 'general:idea'
    assert 'Let me pick dates' in row['note']