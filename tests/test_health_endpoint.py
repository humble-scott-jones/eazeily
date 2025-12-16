
def test_debug_health_endpoint_contract(client):
    response = client.get('/api/debug/health')
    assert response.status_code in (200, 503)

    body = response.get_json()
    assert 'ok' in body
    assert body.get('request_id')
    assert body.get('status') in {'healthy', 'unhealthy'}
    assert 'checks' in body
    assert 'db' in body
    assert 'version' in body
    assert 'timestamp' in body
    assert 'openai' in body['checks']
    assert 'database' in body['checks']

    if body['ok']:
        assert response.status_code == 200
