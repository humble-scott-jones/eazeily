import json
import uuid
import app as togetherly_app


def signup(client, email='user@example.com'):
    return client.post('/api/signup', json={'email': email, 'password': 'secret123'})


def create_template(client, name='Launch kit', scope='personal'):
    payload = {
        'generator': {
            'tone': 'friendly',
            'platforms': ['instagram'],
            'goals': ['Launch'],
            'keywords': ['buzz']
        }
    }
    return client.post('/api/templates', json={
        'name': name,
        'scope': scope,
        'payload': payload,
        'preview': 'Tone: friendly'
    })


def test_templates_crud(client):
    signup(client)

    create_resp = create_template(client)
    assert create_resp.status_code == 201
    created = create_resp.get_json()['template']
    template_id = created['id']

    list_resp = client.get('/api/templates')
    assert list_resp.status_code == 200
    listed = list_resp.get_json()['templates']
    assert len(listed) == 1
    assert listed[0]['name'] == 'Launch kit'

    detail_resp = client.get(f'/api/templates/{template_id}')
    assert detail_resp.status_code == 200
    detail = detail_resp.get_json()['template']
    assert detail['payload']['generator']['tone'] == 'friendly'

    delete_resp = client.delete(f'/api/templates/{template_id}')
    assert delete_resp.status_code == 200

    list_after_delete = client.get('/api/templates')
    assert list_after_delete.status_code == 200
    assert list_after_delete.get_json()['templates'] == []
