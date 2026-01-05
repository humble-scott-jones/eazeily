"""Tests for VoiceProfile model with Secret Sauce fields."""

import json
import pytest


def test_voice_profile_secret_sauce_fields(client):
    """Test that VoiceProfile has all Secret Sauce fields."""
    from models import VoiceProfile, db, User
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Create user
        user = User(email='model_test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        # Create profile with Secret Sauce fields
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business',
            industry='Real Estate',
            target_audience='Local families',
            brand_voice='Professional and friendly',
            key_offer='Free consultation',
            voice_rules='Use y\'all, keep it under 280 characters'
        )
        profile.set_writing_samples(['Sample 1', 'Sample 2', 'Sample 3'])
        
        db.session.add(profile)
        db.session.commit()
        
        # Retrieve and verify
        retrieved = VoiceProfile.query.filter_by(user_id=user.id).first()
        assert retrieved is not None
        assert retrieved.business_name == 'Test Business'
        assert retrieved.industry == 'Real Estate'
        assert retrieved.target_audience == 'Local families'
        assert retrieved.brand_voice == 'Professional and friendly'
        assert retrieved.key_offer == 'Free consultation'
        assert retrieved.voice_rules == 'Use y\'all, keep it under 280 characters'
        
        # Test writing samples methods
        samples = retrieved.get_writing_samples()
        assert len(samples) == 3
        assert samples[0] == 'Sample 1'
        assert samples[1] == 'Sample 2'
        assert samples[2] == 'Sample 3'


def test_voice_profile_writing_samples_json_storage(client):
    """Test that writing samples are stored and retrieved as JSON."""
    from models import VoiceProfile, db, User
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Create user
        user = User(email='json_test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        # Create profile
        profile = VoiceProfile(user_id=user.id)
        
        # Test empty samples
        assert profile.get_writing_samples() == []
        
        # Set samples
        samples = [
            'First sample with special chars: "quotes" & symbols!',
            'Second sample\nwith newlines',
            'Third sample'
        ]
        profile.set_writing_samples(samples)
        db.session.add(profile)
        db.session.commit()
        
        # Retrieve and verify
        retrieved = VoiceProfile.query.filter_by(user_id=user.id).first()
        retrieved_samples = retrieved.get_writing_samples()
        
        assert len(retrieved_samples) == 3
        assert retrieved_samples[0] == samples[0]
        assert retrieved_samples[1] == samples[1]
        assert retrieved_samples[2] == samples[2]


def test_voice_profile_backward_compatibility(client):
    """Test that old profiles without Secret Sauce fields still work."""
    from models import VoiceProfile, db, User
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Create user
        user = User(email='compat_test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        # Create profile with only old fields
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Old Business',
            industry='general'
        )
        profile.set_defaults({'style_guide': 'Professional tone'})
        profile.set_examples(['Old example 1', 'Old example 2'])
        
        db.session.add(profile)
        db.session.commit()
        
        # Retrieve and verify old methods still work
        retrieved = VoiceProfile.query.filter_by(user_id=user.id).first()
        assert retrieved.get_defaults()['style_guide'] == 'Professional tone'
        assert len(retrieved.get_examples()) == 2
        
        # New fields should be None/empty
        assert retrieved.target_audience is None
        assert retrieved.brand_voice is None
        assert retrieved.key_offer is None
        assert retrieved.voice_rules is None
        assert retrieved.get_writing_samples() == []


def test_voice_profile_handles_empty_writing_samples(client):
    """Test that empty writing samples are handled correctly."""
    from models import VoiceProfile, db, User
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Create user
        user = User(email='empty_samples@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        # Create profile with empty samples
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test'
        )
        profile.set_writing_samples([])
        
        db.session.add(profile)
        db.session.commit()
        
        # Retrieve and verify
        retrieved = VoiceProfile.query.filter_by(user_id=user.id).first()
        assert retrieved.get_writing_samples() == []


def test_voice_profile_nullable_fields(client):
    """Test that Secret Sauce fields can be null."""
    from models import VoiceProfile, db, User
    from app import create_app
    
    app = create_app()
    with app.app_context():
        # Create user
        user = User(email='nullable_test@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        # Create minimal profile
        profile = VoiceProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        # Retrieve and verify nulls are handled
        retrieved = VoiceProfile.query.filter_by(user_id=user.id).first()
        assert retrieved.business_name is None
        assert retrieved.industry is None
        assert retrieved.target_audience is None
        assert retrieved.brand_voice is None
        assert retrieved.key_offer is None
        assert retrieved.voice_rules is None
        assert retrieved.get_writing_samples() == []
