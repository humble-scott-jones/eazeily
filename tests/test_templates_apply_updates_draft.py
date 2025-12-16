import json
import uuid
from datetime import datetime, timezone
import app as togetherly_app


def test_templates_apply_updates_draft(client):
    signup_resp = client.post('/api/signup', json={'email': 'apply@example.com', 'password': 'secret123'})
    user_id = signup_resp.get_json()['id']

    template_payload = {
        'generator': {
            'tone': 'playful',
            'platforms': ['linkedin'],
            'goals': ['Hiring'],
            'keywords': ['team growth']
        },
        'draft': [
            {'id': 'hook', 'heading': 'Hook', 'text': 'New hook from template'},
            {'id': 'cta', 'heading': 'CTA', 'text': 'Join us today'}
        ]
    }
    template_resp = client.post('/api/templates', json={
        'name': 'Team update',
        'payload': template_payload,
        'preview': 'Tone: playful'
    })
    template_id = template_resp.get_json()['template']['id']

    draft_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    with client.application.app_context():
        db = togetherly_app.get_db()
        db.execute(
            'INSERT INTO team_drafts (id, owner_user_id, title, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
            (draft_id, user_id, 'Initial Draft', json.dumps([{'id': 'hook', 'text': 'Old hook'}]), now_iso, now_iso)
        )
        db.commit()

    apply_resp = client.post(f'/api/templates/{template_id}/apply', json={'draft_id': draft_id})
    assert apply_resp.status_code == 200
    applied = apply_resp.get_json()['draft']
    assert applied['content'][0]['text'] == 'New hook from template'

    undo_resp = client.post(f'/api/drafts/{draft_id}/undo-template')
    assert undo_resp.status_code == 200
    reverted = undo_resp.get_json()['draft']
    assert reverted['content'][0]['text'] == 'Old hook'
