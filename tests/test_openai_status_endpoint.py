
def test_openai_status_endpoint_returns_contract(client):
    response = client.get('/api/debug/openai-status')
    assert response.status_code == 200

    body = response.get_json()
    assert body['ok'] is True
    assert body.get('request_id')
    assert body.get('status') in {'enabled', 'disabled'}
    assert isinstance(body.get('configured'), bool)
    assert isinstance(body.get('kill_switch_active'), bool)
    assert isinstance(body.get('client_ready'), bool)
