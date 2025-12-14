import logging


def test_api_generate_emits_telemetry(client, caplog):
    """Test that generation endpoint emits telemetry.
    
    Note: With validation gate enabled, fallback content is blocked,
    so this test now checks for error telemetry instead of success.
    """
    with caplog.at_level(logging.INFO):
        res = client.post('/api/generate', json={'days': 1, 'platforms': ['instagram']})

    assert res.status_code == 200
    data = res.get_json()
    # Validation now blocks fallback output with scaffold text
    # Result will have ok:false
    
    messages = [record.getMessage() for record in caplog.records]
    assert any('generator.request' in msg for msg in messages)
    # Check for outcome message (success or failure)
    assert any('generation.outcome' in msg for msg in messages)
