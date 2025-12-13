import logging


def test_api_generate_emits_telemetry(client, caplog):
    with caplog.at_level(logging.INFO):
        res = client.post('/api/generate', json={'days': 1, 'platforms': ['instagram']})

    assert res.status_code == 200
    data = res.get_json()
    assert data and data.get('ok') is True

    messages = [record.getMessage() for record in caplog.records]
    assert any('generator.request' in msg for msg in messages)
    assert any('generator.success' in msg for msg in messages)
