"""Test suite for queue API endpoints."""

import pytest
import json


def test_queue_page_renders(client):
    """The /queue page should render successfully."""
    resp = client.get('/queue')
    assert resp.status_code == 200
    assert b'Queue' in resp.data


def test_queue_page_shows_timezone(client):
    """The /queue page should display timezone information."""
    # Set a timezone preference first
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-queue-tz'
    
    client.post('/api/queue', json={
        'timezone': 'America/New_York',
        'items': []
    })
    
    resp = client.get('/queue')
    assert resp.status_code == 200
    assert b'America/New_York' in resp.data


def test_api_queue_get_empty(client):
    """GET /api/queue should return empty items for new session."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-empty-queue'
    
    resp = client.get('/api/queue')
    assert resp.status_code == 200
    
    body = resp.get_json()
    assert body['ok'] is True
    assert isinstance(body['items'], list)
    assert len(body['items']) == 0
    assert 'timezone' in body
    assert 'bulk_actions' in body
    assert 'guardrails' in body


def test_api_queue_post_single_item(client):
    """POST /api/queue should create a new queue item."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-add-item'
    
    payload = {
        'timezone': 'America/Los_Angeles',
        'items': [{
            'platform': 'instagram',
            'caption': 'Test post content',
            'status': 'queued',
            'metadata': {'test': True}
        }]
    }
    
    resp = client.post('/api/queue', json=payload)
    assert resp.status_code == 201
    
    body = resp.get_json()
    assert body['ok'] is True
    assert body.get('request_id')
    assert len(body['items']) == 1
    
    item = body['items'][0]
    assert item['platform'] == 'instagram'
    assert item['caption'] == 'Test post content'
    assert item['status'] == 'queued'
    assert item['timezone'] == 'America/Los_Angeles'
    assert item['metadata'] == {'test': True}
    assert 'id' in item
    assert 'created_at' in item
    assert 'updated_at' in item


def test_api_queue_post_multiple_items(client):
    """POST /api/queue should handle multiple items at once."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-multi-items'
    
    payload = {
        'timezone': 'UTC',
        'items': [
            {'platform': 'instagram', 'caption': 'Post 1'},
            {'platform': 'facebook', 'caption': 'Post 2'},
            {'platform': 'twitter', 'caption': 'Post 3'},
        ]
    }
    
    resp = client.post('/api/queue', json=payload)
    assert resp.status_code == 201
    
    body = resp.get_json()
    assert body['ok'] is True
    assert len(body['items']) == 3
    assert body['timezone'] == 'UTC'


def test_api_queue_post_with_scheduled_at(client):
    """POST /api/queue should accept scheduled_at timestamps."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-scheduled'
    
    payload = {
        'items': [{
            'platform': 'linkedin',
            'caption': 'Scheduled post',
            'scheduled_at': '2025-12-25T10:00:00Z'
        }]
    }
    
    resp = client.post('/api/queue', json=payload)
    assert resp.status_code == 201
    
    body = resp.get_json()
    assert body['ok'] is True
    item = body['items'][0]
    assert item['status'] == 'scheduled'
    assert item['scheduled_at'] == '2025-12-25T10:00:00+00:00'


def test_api_queue_post_defaults_status_to_queued(client):
    """Items without scheduled_at should default to 'queued' status."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-default-status'
    
    payload = {
        'items': [{'platform': 'tiktok', 'caption': 'No schedule'}]
    }
    
    resp = client.post('/api/queue', json=payload)
    assert resp.status_code == 201
    
    body = resp.get_json()
    item = body['items'][0]
    assert item['status'] == 'queued'
    assert item['scheduled_at'] is None


def test_api_queue_get_retrieves_posted_items(client):
    """GET /api/queue should return previously posted items."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-retrieve'
    
    # Add items
    post_resp = client.post('/api/queue', json={
        'items': [
            {'platform': 'instagram', 'caption': 'Item 1'},
            {'platform': 'facebook', 'caption': 'Item 2'},
        ]
    })
    assert post_resp.status_code == 201
    
    # Retrieve items
    get_resp = client.get('/api/queue')
    assert get_resp.status_code == 200
    
    body = get_resp.get_json()
    assert body['ok'] is True
    assert len(body['items']) == 2


def test_api_queue_items_scoped_per_owner(client):
    """Queue items should be scoped per owner (session isolation)."""
    # Owner 1
    with client.session_transaction() as sess:
        sess['profile_id'] = 'owner-1'
    
    client.post('/api/queue', json={
        'items': [{'platform': 'instagram', 'caption': 'Owner 1 post'}]
    })
    
    # Owner 2
    with client.session_transaction() as sess:
        sess['profile_id'] = 'owner-2'
    
    client.post('/api/queue', json={
        'items': [{'platform': 'facebook', 'caption': 'Owner 2 post'}]
    })
    
    # Owner 1 should only see their items
    with client.session_transaction() as sess:
        sess['profile_id'] = 'owner-1'
    
    resp = client.get('/api/queue')
    body = resp.get_json()
    assert len(body['items']) == 1
    assert body['items'][0]['caption'] == 'Owner 1 post'


def test_api_queue_retry_updates_status(client):
    """POST /api/queue/<id>/retry should reset failed items to queued."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-retry'
    
    # Create a failed item
    post_resp = client.post('/api/queue', json={
        'items': [{
            'platform': 'twitter',
            'caption': 'Failed post',
            'status': 'failed',
            'failure_reason': 'Network timeout'
        }]
    })
    item_id = post_resp.get_json()['items'][0]['id']
    
    # Retry the item
    retry_resp = client.post(f'/api/queue/{item_id}/retry')
    assert retry_resp.status_code == 200
    
    body = retry_resp.get_json()
    assert body['ok'] is True
    assert body['item']['status'] == 'queued'
    assert body['item']['failure_reason'] == ''


def test_api_queue_retry_not_found(client):
    """POST /api/queue/<id>/retry should return 404 for non-existent items."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-not-found'
    
    resp = client.post('/api/queue/nonexistent-id/retry')
    assert resp.status_code == 404
    
    body = resp.get_json()
    assert body['ok'] is False
    assert 'error' in body


def test_api_queue_retry_respects_owner_scoping(client):
    """Retry should only work for items owned by the current session."""
    # Owner 1 creates an item
    with client.session_transaction() as sess:
        sess['profile_id'] = 'owner-retry-1'
    
    post_resp = client.post('/api/queue', json={
        'items': [{'platform': 'instagram', 'caption': 'Owner 1 item'}]
    })
    item_id = post_resp.get_json()['items'][0]['id']
    
    # Owner 2 tries to retry Owner 1's item
    with client.session_transaction() as sess:
        sess['profile_id'] = 'owner-retry-2'
    
    resp = client.post(f'/api/queue/{item_id}/retry')
    assert resp.status_code == 404
    assert resp.get_json()['ok'] is False


def test_api_queue_timezone_persistence(client):
    """Timezone preference should persist across requests."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-tz-persist'
    
    # Set timezone
    client.post('/api/queue', json={
        'timezone': 'Europe/London',
        'items': []
    })
    
    # Verify it persists on GET
    get_resp = client.get('/api/queue')
    assert get_resp.get_json()['timezone'] == 'Europe/London'
    
    # Add item without timezone, should use saved preference
    post_resp = client.post('/api/queue', json={
        'items': [{'platform': 'linkedin', 'caption': 'Test'}]
    })
    assert post_resp.get_json()['timezone'] == 'Europe/London'


def test_api_queue_handles_dict_as_single_item(client):
    """API should accept a single dict as items (not just arrays)."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-dict-item'
    
    payload = {
        'items': {'platform': 'instagram', 'caption': 'Single item as dict'}
    }
    
    resp = client.post('/api/queue', json=payload)
    assert resp.status_code == 201
    
    body = resp.get_json()
    assert len(body['items']) == 1


def test_api_queue_ignores_invalid_items(client):
    """API should skip non-dict items in the items array."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-invalid-items'
    
    payload = {
        'items': [
            {'platform': 'instagram', 'caption': 'Valid'},
            'invalid-string',
            123,
            None,
            {'platform': 'facebook', 'caption': 'Also valid'},
        ]
    }
    
    resp = client.post('/api/queue', json=payload)
    assert resp.status_code == 201
    
    body = resp.get_json()
    # Should only create 2 items (the valid dicts)
    assert len(body['items']) == 2


def test_api_queue_handles_empty_timezone(client):
    """Empty timezone strings should be handled gracefully."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-empty-tz'
    
    payload = {
        'timezone': '   ',
        'items': [{'platform': 'twitter', 'caption': 'Test'}]
    }
    
    resp = client.post('/api/queue', json=payload)
    assert resp.status_code == 201
    # Empty/whitespace timezone should not be persisted
    assert resp.get_json()['timezone'] == ''


def test_api_queue_normalizes_timestamps(client):
    """Timestamps should be normalized to ISO format with timezone."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-normalize-ts'
    
    # Test with Unix timestamp
    payload = {
        'items': [{
            'platform': 'instagram',
            'caption': 'Unix timestamp',
            'scheduled_at': 1735128000  # 2024-12-25 12:00:00 UTC
        }]
    }
    
    resp = client.post('/api/queue', json=payload)
    assert resp.status_code == 201
    
    item = resp.get_json()['items'][0]
    assert item['scheduled_at'] is not None
    assert 'T' in item['scheduled_at']  # ISO format
    assert '+' in item['scheduled_at'] or 'Z' in item['scheduled_at']  # Has timezone


def test_api_queue_items_ordered_by_created_at(client):
    """GET /api/queue should return items in descending created_at order."""
    with client.session_transaction() as sess:
        sess['profile_id'] = 'test-ordering'
    
    # Add items in sequence
    for i in range(3):
        client.post('/api/queue', json={
            'items': [{'platform': 'instagram', 'caption': f'Post {i}'}]
        })
    
    resp = client.get('/api/queue')
    items = resp.get_json()['items']
    
    # Most recent should be first
    assert items[0]['caption'] == 'Post 2'
    assert items[1]['caption'] == 'Post 1'
    assert items[2]['caption'] == 'Post 0'
