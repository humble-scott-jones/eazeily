import re


def test_request_id_in_header_and_body(client):
    response = client.get('/health')
    assert response.status_code in (200, 503)

    # Header should always include a request id
    rid_header = response.headers.get('X-Request-Id')
    assert rid_header
    assert re.fullmatch(r"[0-9a-f]{8}", rid_header)

    data = response.get_json()
    assert data
    assert data.get('request_id') == rid_header


def test_request_id_added_to_non_api_json(client):
    response = client.get('/healthz')
    assert response.status_code == 200

    data = response.get_json()
    assert data
    assert 'request_id' in data
