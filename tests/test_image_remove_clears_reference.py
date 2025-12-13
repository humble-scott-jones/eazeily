from io import BytesIO
import os

import app as appmod


def _configure_upload_dir(tmp_path):
    upload_dir = tmp_path / "uploads"
    appmod.UPLOAD_DIR = str(upload_dir)
    appmod.app.config['UPLOAD_DIR'] = str(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)


def _upload_sample(client):
    png_bytes = b"\x89PNG\r\n\x1a\n" + (b'\x00' * 64)
    resp = client.post(
        '/api/uploads',
        data={'file': (BytesIO(png_bytes), 'keep.png')},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 200
    return resp.get_json()['upload']


def test_deleting_upload_blocks_image_use(client, tmp_path):
    _configure_upload_dir(tmp_path)
    upload = _upload_sample(client)

    # Delete and ensure it is gone on disk and in DB
    resp = client.delete(f"/api/uploads/{upload['id']}")
    assert resp.status_code == 200

    with appmod.app.app_context():
        row = appmod.get_db().execute('SELECT id FROM uploads WHERE id = ?', (upload['id'],)).fetchone()
    assert row is None
    assert not os.path.exists(os.path.join(appmod.app.config['UPLOAD_DIR'], f"{upload['id']}.png"))

    # Attempt to generate with a missing upload returns a clear error
    rv = client.post('/api/generate', json={'days': 1, 'image_upload_id': upload['id']})
    assert rv.status_code == 410
    body = rv.get_json()
    assert body['error']['code'] == 'image_missing'
    assert 'upload it again' in body['error']['message']
