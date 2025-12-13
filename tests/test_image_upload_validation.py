import os
from io import BytesIO

import app as appmod


def _configure_upload_dir(tmp_path):
    upload_dir = tmp_path / "uploads"
    appmod.UPLOAD_DIR = str(upload_dir)
    appmod.app.config['UPLOAD_DIR'] = str(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)


def test_rejects_non_image_upload(client, tmp_path):
    _configure_upload_dir(tmp_path)
    resp = client.post('/api/uploads', data={'file': (BytesIO(b'hello'), 'note.txt')}, content_type='multipart/form-data')
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error']['message'].startswith('Only image uploads')


def test_rejects_oversized_upload(client, tmp_path):
    _configure_upload_dir(tmp_path)
    big_payload = b'a' * (appmod.MAX_IMAGE_UPLOAD_BYTES + 5)
    resp = client.post(
        '/api/uploads',
        data={'file': (BytesIO(big_payload), 'huge.png')},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert '5MB' in body['error']['message']


def test_missing_file_returns_clear_error(client, tmp_path):
    _configure_upload_dir(tmp_path)
    resp = client.post('/api/uploads', data={}, content_type='multipart/form-data')
    assert resp.status_code == 400
    assert resp.get_json()['error']['message'] == 'No file provided.'
