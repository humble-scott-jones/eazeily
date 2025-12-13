import os
from io import BytesIO

import app as appmod


def _configure_upload_dir(tmp_path):
    upload_dir = tmp_path / "uploads"
    appmod.UPLOAD_DIR = str(upload_dir)
    appmod.app.config['UPLOAD_DIR'] = str(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)


def test_serve_uploaded_file_success(client, tmp_path):
    """Test successful file serving with correct mimetype."""
    _configure_upload_dir(tmp_path)
    png_bytes = b"\x89PNG\r\n\x1a\n" + (b'\x00' * 128)
    
    # Upload a file
    resp = client.post(
        '/api/uploads',
        data={'file': (BytesIO(png_bytes), 'sample.png')},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 200
    upload = resp.get_json()['upload']
    upload_id = upload['id']
    url = upload['url']
    
    # Serve the file
    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.data == png_bytes
    assert 'image/png' in resp.content_type


def test_serve_uploaded_file_not_found_invalid_id(client, tmp_path):
    """Test 404 response when upload_id doesn't exist."""
    _configure_upload_dir(tmp_path)
    
    resp = client.get('/uploads/invalid-id/test.png')
    assert resp.status_code == 404
    assert resp.content_type == 'text/plain; charset=utf-8'
    assert b'Upload not found.' in resp.data


def test_serve_uploaded_file_not_found_filename_mismatch(client, tmp_path):
    """Test 404 response when filename doesn't match storage_name."""
    _configure_upload_dir(tmp_path)
    png_bytes = b"\x89PNG\r\n\x1a\n" + (b'\x00' * 128)
    
    # Upload a file
    resp = client.post(
        '/api/uploads',
        data={'file': (BytesIO(png_bytes), 'sample.png')},
        content_type='multipart/form-data'
    )
    assert resp.status_code == 200
    upload = resp.get_json()['upload']
    upload_id = upload['id']
    
    # Try to access with wrong filename
    resp = client.get(f'/uploads/{upload_id}/wrong-filename.png')
    assert resp.status_code == 404
    assert resp.content_type == 'text/plain; charset=utf-8'
    assert b'Upload not found.' in resp.data


def test_serve_uploaded_file_missing_path_in_db(client, tmp_path):
    """Test proper handling of missing path in database record."""
    _configure_upload_dir(tmp_path)
    
    # Create a database record without a path
    with appmod.app.app_context():
        db = appmod.get_db()
        upload_id = 'test-no-path-id'
        db.execute(
            'INSERT INTO uploads (id, filename, mime, size_bytes, path) VALUES (?, ?, ?, ?, ?)',
            (upload_id, 'test.png', 'image/png', 100, None)
        )
        db.commit()
    
    # Try to serve the file
    resp = client.get(f'/uploads/{upload_id}/test.png')
    assert resp.status_code == 404
    assert resp.content_type == 'text/plain; charset=utf-8'
    assert b'Upload not found.' in resp.data
