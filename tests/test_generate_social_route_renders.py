import pytest


def test_generate_social_route_renders(client):
    resp = client.get('/generate/social')
    assert resp.status_code == 200
    assert b"Generate plan" in resp.data
    assert b"What will be generated" in resp.data
