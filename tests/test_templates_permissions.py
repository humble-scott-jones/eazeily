import json
import uuid
from datetime import datetime, timezone
import app as togetherly_app


def _insert_draft(app_ctx, draft_id, owner_id, text):
    db = togetherly_app.get_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    db.execute(
        'INSERT INTO team_drafts (id, owner_user_id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
        (draft_id, owner_id, 'Secure Draft', json.dumps([{'id': 'section', 'text': text}]), now_iso, now_iso)
    )
    db.commit()


def test_templates_permissions(client):
    first_resp = client.post('/api/signup', json={'email': 'owner@example.com', 'password': 'secret123'})
    owner_id = first_resp.get_json()['id']
    template_resp = client.post('/api/templates', json={
        'name': 'Owner only',
        'payload': {'generator': {'tone': 'friendly'}},
        'preview': 'Tone: friendly'
    })
    template_id = template_resp.get_json()['template']['id']

    client.post('/api/logout')
    second_resp = client.post('/api/signup', json={'email': 'other@example.com', 'password': 'secret123'})
    other_id = second_resp.get_json()['id']

    forbidden_detail = client.get(f'/api/templates/{template_id}')
    assert forbidden_detail.status_code == 404

    draft_id = str(uuid.uuid4())
    with client.application.app_context():
        _insert_draft(client.application, draft_id, other_id, 'other draft')

    apply_resp = client.post(f'/api/templates/{template_id}/apply', json={'draft_id': draft_id})
    assert apply_resp.status_code == 404

    list_resp = client.get('/api/templates')
    assert list_resp.status_code == 200
    assert list_resp.get_json()['templates'] == []
