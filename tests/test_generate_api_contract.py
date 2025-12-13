def test_generate_response_contract_success(client):
    """Successful generations should always include request metadata and posts."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'contract-success'

    resp = client.post('/api/generate', json={'days': 1})
    assert resp.status_code == 200

    body = resp.get_json()
    assert body['ok'] is True
    assert body.get('request_id')
    assert isinstance(body.get('posts'), list)
    assert len(body['posts']) > 0


def test_generate_response_contract_error_includes_request_id(client):
    """Error responses must also surface the request ID for debugging."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'contract-error'

    resp = client.post('/api/generate', json={'days': 1, 'image_data_url': 'data:image/png;base64,'})
    assert resp.status_code in (400, 503)

    body = resp.get_json()
    assert body['ok'] is False
    assert body.get('request_id')
    assert 'error' in body
    assert 'message' in body['error']
