import os
from io import BytesIO

import app as appmod


def _configure_upload_dir(tmp_path):
    upload_dir = tmp_path / "uploads"
    appmod.UPLOAD_DIR = str(upload_dir)
    appmod.app.config['UPLOAD_DIR'] = str(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)


def test_image_upload_persists_file_and_metadata(client, tmp_path):
    _configure_upload_dir(tmp_path)
    png_bytes = b"\x89PNG\r\n\x1a\n" + (b'\x00' * 128)
    resp = client.post(
        '/api/uploads',
        data={'file': (BytesIO(png_bytes), 'sample.png')},
        content_type='multipart/form-data'
    )

    assert resp.status_code == 200
    payload = resp.get_json()
    upload = payload['upload']
    assert upload['id']
    assert upload['filename'] == 'sample.png'
    assert upload['size_bytes'] == len(png_bytes)
    path = os.path.join(appmod.app.config['UPLOAD_DIR'], f"{upload['id']}.png")
    assert os.path.exists(path)

    # DB row exists
    with appmod.app.app_context():
        row = appmod.get_db().execute('SELECT filename, size_bytes FROM uploads WHERE id = ?', (upload['id'],)).fetchone()
    assert row is not None
    assert row['size_bytes'] == len(png_bytes)
