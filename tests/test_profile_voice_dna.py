"""Test voice_dna field in VoiceProfile model and API endpoints."""

import pytest
import json


def test_voice_profile_voice_dna_methods(app):
    """Test set_voice_dna and get_voice_dna helper methods."""
    from models import db, VoiceProfile, User
    
    with app.app_context():
        # Create a test user
        user = User(email='test@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        # Create a profile
        profile = VoiceProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        # Test setting voice_dna
        voice_dna_data = {
            'voice_rhythm': 'short and punchy',
            'emoji_style': 'minimal',
            'forbidden_words': ['jargon', 'buzzwords'],
            'signature_signoffs': ['Cheers,', 'Best,'],
            'sentence_structure': 'starts with verbs'
        }
        profile.set_voice_dna(voice_dna_data)
        db.session.commit()
        
        # Test getting voice_dna
        retrieved_dna = profile.get_voice_dna()
        assert retrieved_dna == voice_dna_data
        assert retrieved_dna['voice_rhythm'] == 'short and punchy'
        assert retrieved_dna['emoji_style'] == 'minimal'
        assert retrieved_dna['forbidden_words'] == ['jargon', 'buzzwords']
        assert retrieved_dna['signature_signoffs'] == ['Cheers,', 'Best,']
        assert retrieved_dna['sentence_structure'] == 'starts with verbs'


def test_voice_dna_empty_default(app):
    """Test that get_voice_dna returns empty dict when voice_dna is None."""
    from models import db, VoiceProfile, User
    
    with app.app_context():
        # Create a test user
        user = User(email='test2@example.com')
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        
        # Create a profile without setting voice_dna
        profile = VoiceProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        # Test that get_voice_dna returns empty dict
        retrieved_dna = profile.get_voice_dna()
        assert retrieved_dna == {}


def test_profile_api_includes_voice_dna(client):
    """Test that profile API GET endpoint includes voice_dna field."""
    # Sign up
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create profile with voice_dna
    profile_data = {
        'company': 'Test Business',
        'industry': 'Software / Tech / Startup',
        'voice_dna': {
            'voice_rhythm': 'long and flowing',
            'emoji_style': 'heaps of ✨',
            'forbidden_words': ['synergy', 'leverage'],
            'signature_signoffs': ['Stay awesome!'],
            'sentence_structure': 'uses questions'
        }
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Retrieve profile
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    profile = data['profile']
    assert 'voice_dna' in profile
    assert profile['voice_dna']['voice_rhythm'] == 'long and flowing'
    assert profile['voice_dna']['emoji_style'] == 'heaps of ✨'
    assert profile['voice_dna']['forbidden_words'] == ['synergy', 'leverage']
    assert profile['voice_dna']['signature_signoffs'] == ['Stay awesome!']
    assert profile['voice_dna']['sentence_structure'] == 'uses questions'


def test_profile_api_post_saves_voice_dna(client):
    """Test that profile API POST endpoint saves voice_dna correctly."""
    # Sign up
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create profile with voice_dna
    voice_dna_data = {
        'voice_rhythm': 'mixed cadence',
        'emoji_style': 'only at end',
        'forbidden_words': ['corporate speak'],
        'signature_signoffs': ['Cheers,'],
        'sentence_structure': 'declarative statements'
    }
    
    profile_data = {
        'company': 'Acme Corp',
        'voice_dna': voice_dna_data
    }
    
    response = client.post('/api/profile', json=profile_data)
    assert response.status_code == 200
    
    # Verify it was saved by retrieving
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    assert data['profile']['voice_dna'] == voice_dna_data


def test_profile_v2_includes_voice_dna(client):
    """Test that profile_v2 endpoint includes voice_dna field."""
    # Sign up
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create profile with voice_dna
    profile_data = {
        'company': 'Startup Inc',
        'voice_dna': {
            'voice_rhythm': 'short and punchy',
            'emoji_style': 'scattered throughout'
        }
    }
    
    client.post('/api/profile', json=profile_data)
    
    # Retrieve via profile_v2
    response = client.get('/api/profile_v2')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    profile = data['profile']
    assert 'voice_dna' in profile
    assert profile['voice_dna']['voice_rhythm'] == 'short and punchy'
    assert profile['voice_dna']['emoji_style'] == 'scattered throughout'


def test_empty_profile_has_default_voice_dna(client):
    """Test that empty profile returns empty dict for voice_dna."""
    # Sign up (creates user but no profile yet)
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Get profile before any data is saved
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    profile = data['profile']
    assert profile['voice_dna'] == {}


def test_voice_dna_merge_on_update(client):
    """Test that updating voice_dna merges with existing data."""
    # Sign up
    client.post('/api/signup', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    # Create profile with initial voice_dna
    initial_data = {
        'company': 'Test Co',
        'voice_dna': {
            'voice_rhythm': 'short and punchy',
            'emoji_style': 'minimal'
        }
    }
    
    response = client.post('/api/profile', json=initial_data)
    assert response.status_code == 200
    
    # Update with additional voice_dna fields
    update_data = {
        'voice_dna': {
            'emoji_style': 'heaps of ✨',  # Update existing
            'forbidden_words': ['jargon']  # Add new field
        }
    }
    
    response = client.post('/api/profile', json=update_data)
    assert response.status_code == 200
    
    # Verify the merge
    response = client.get('/api/profile')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    voice_dna = data['profile']['voice_dna']
    # Should have updated emoji_style, but voice_rhythm should be gone (replaced)
    assert voice_dna == {
        'emoji_style': 'heaps of ✨',
        'forbidden_words': ['jargon']
    }
