import pytest
from app import app


def test_profile_api_contract(client):
    payload = {
        'company': 'Contract Co',
        'tone': 'playful',
        'platforms': ['instagram', 'linkedin']
    }
    create_resp = client.post('/api/profile', json=payload)
    assert create_resp.status_code == 200
    created_body = create_resp.get_json()
    assert created_body.get('ok') is True
    assert created_body.get('request_id')

    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('ok') is True
    assert body.get('request_id')
    profile = body.get('profile')
    assert isinstance(profile, dict)

    for key in ('company', 'industry', 'tone', 'platforms', 'timezone'):
        assert key in profile
    assert profile.get('company').lower().startswith('contract')
    assert isinstance(profile.get('platforms'), list)
    assert isinstance(profile.get('brand_keywords'), list)
    assert isinstance(profile.get('goals'), list)
    assert profile.get('timezone') == ''
    assert profile.get('industry') == ''
    assert profile.get('tone') == 'playful'


def test_profile_missing_fields_are_defaults(client):
    resp = client.get('/api/profile')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body.get('ok') is True
    profile = body.get('profile') or {}
    assert profile.get('company') == ''
    assert profile.get('industry') == ''
    assert profile.get('tone') == ''
    assert profile.get('platforms') == []
    assert profile.get('timezone') == ''
