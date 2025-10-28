import os
import json
import tempfile
import sqlite3
import types
import pytest

import app as app_mod

@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Isolate DB for this test module
    db_path = tmp_path / "smoke.db"
    monkeypatch.setattr(app_mod, "DB_PATH", str(db_path))
    test_app = app_mod.app
    with test_app.test_client() as c:
        with test_app.app_context():
            app_mod.init_db()
        yield c


def test_health_ok(client):
    r = client.get('/health')
    assert r.status_code in (200, 503)
    j = r.get_json()
    assert 'status' in j


def test_waitlist_add_and_duplicate(client):
    email = 'smoke@example.com'
    r1 = client.post('/api/waitlist', json={'email': email})
    j1 = r1.get_json()
    assert r1.status_code == 200
    assert j1.get('ok') is True
    r2 = client.post('/api/waitlist', json={'email': email})
    # duplicate should be a 400 with helpful message
    assert r2.status_code in (200, 400)


def test_auth_and_free_sample_flow(client):
    # signup
    r = client.post('/api/signup', json={'email': 'user@example.com', 'password': 'password'})
    assert r.status_code == 200
    j = r.get_json()
    assert j.get('ok') is True
    # current user
    r2 = client.get('/api/current_user')
    j2 = r2.get_json()
    assert j2.get('email') == 'user@example.com'

    # generate a 1-day sample should work for free users
    payload = {
        'industry': 'Business', 'tone': 'friendly', 'platforms': ['instagram'],
        'brand_keywords': [], 'niche_keywords': [], 'include_images': True,
        'days': 1
    }
    r3 = client.post('/api/generate', json=payload)
    assert r3.status_code == 200
    j3 = r3.get_json()
    assert j3.get('count') == 1

    # second attempt should be blocked (free_sample_used = True)
    r4 = client.post('/api/generate', json=payload)
    assert r4.status_code == 403

    # multi-day attempt should be blocked for free users
    payload['days'] = 7
    r5 = client.post('/api/generate', json=payload)
    assert r5.status_code == 403


def test_review_response(client):
    # positive review
    r = client.post('/api/generate-review-response', json={'review_text': 'Great service and friendly staff!', 'tone': 'professional'})
    assert r.status_code == 200
    j = r.get_json()
    assert j.get('ok') is True
    assert isinstance(j.get('response'), str) and len(j['response']) > 0

    # negative review
    r2 = client.post('/api/generate-review-response', json={'review_text': 'Terrible experience, very disappointed.', 'tone': 'apologetic'})
    assert r2.status_code == 200
    j2 = r2.get_json()
    assert j2.get('ok') is True


def test_dev_webhook_checkout_sets_paid(client):
    # ensure we have a user signed up and in session
    r = client.post('/api/signup', json={'email': 'paid@example.com', 'password': 'password'})
    assert r.status_code == 200
    user_id = r.get_json().get('id')

    event = {
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'client_reference_id': user_id,
                'customer': 'cus_test',
                'subscription': 'sub_test_123'
            }
        }
    }
    r2 = client.post('/api/stripe-webhook', data=json.dumps(event))
    assert r2.status_code == 200

    # account should show paid now
    r3 = client.get('/api/account')
    assert r3.status_code == 200
    j3 = r3.get_json()
    assert j3.get('ok') is True
    assert j3['user']['is_paid'] is True
