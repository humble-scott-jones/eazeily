import pytest
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            # Mock session
            with client.session_transaction() as sess:
                sess['user_id'] = 'test_user'
        yield client

def test_voice_analyze(client):
    data = {
        'samples': [
            "This is a test sentence. It is short.",
            "Another sentence here! With some excitement."
        ]
    }
    resp = client.post('/api/voice/analyze', json=data)
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data['ok'] is True
    assert 'profile' in json_data
    assert 'style_instruction' in json_data['profile']

@patch('requests.get')
def test_voice_scrape(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = """
    <html>
        <body>
            <p>This is a long enough paragraph to be scraped by the tool. It has plenty of words.</p>
            <p>Short.</p>
            <div>Another container with some text content that should be picked up.</div>
        </body>
    </html>
    """
    mock_get.return_value = mock_resp
    
    data = {'url': 'http://example.com'}
    resp = client.post('/api/voice/scrape', json=data)
    
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert json_data['ok'] is True
    assert len(json_data['samples']) >= 1
    # The order might vary or sorting might affect it, but we expect at least one long sample
    assert any("This is a long enough paragraph" in s for s in json_data['samples'])
