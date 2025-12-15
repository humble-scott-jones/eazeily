def test_template_name_required(client):
    client.post('/api/signup', json={'email': 'namecheck@example.com', 'password': 'secret123'})
    resp = client.post('/api/templates', json={'payload': {'generator': {}}})
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['ok'] is False
    assert 'Name is required' in data['error']
