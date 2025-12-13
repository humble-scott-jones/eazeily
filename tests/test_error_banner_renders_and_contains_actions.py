PATHS = ["/generate/social", "/generate/reviews"]


def test_error_banner_has_actions(client):
    for path in PATHS:
        resp = client.get(path)
        assert resp.status_code == 200
        html = resp.data.decode()
        assert 'data-error-banner' in html
        assert 'data-error-retry' in html
        assert 'data-error-copy' in html
