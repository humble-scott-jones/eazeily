"""
Tests for the database repair script.
"""
import pytest
from models import VoiceProfile, User, db


class TestRepairScript:
    """Test the repair_malformed_json.py script functionality."""
    
    @pytest.fixture
    def app_context(self, client):
        """Provide Flask app context for database operations."""
        from app import create_app
        test_app = create_app()
        with test_app.app_context():
            yield test_app
    
    def test_repair_script_via_normalize_method(self, app_context):
        """Test the normalize_json_fields method that the repair script uses."""
        # Create a user and profile
        user = User(email='repair_test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business'
        )
        
        # Corrupt JSON fields
        profile.platforms = '[invalid json'
        profile.brand_keywords = '{"not": "a list"}'
        profile.goals = '["goal1"'
        db.session.add(profile)
        db.session.commit()
        
        profile_id = profile.id
        
        # Normalize the fields
        repaired = profile.normalize_json_fields()
        db.session.commit()
        
        # Verify repairs were made
        assert len(repaired) == 3
        assert 'platforms' in repaired
        assert 'brand_keywords' in repaired
        assert 'goals' in repaired
        
        # Verify fields are now valid
        profile = VoiceProfile.query.get(profile_id)
        assert profile.get_platforms() == []
        assert profile.get_brand_keywords() == []
        assert profile.get_goals() == []
        
        # Verify JSON is valid
        import json
        assert json.loads(profile.platforms) == []
        assert json.loads(profile.brand_keywords) == []
        assert json.loads(profile.goals) == []
    
    def test_repair_preserves_valid_data(self, app_context):
        """Test that repair doesn't change valid data."""
        user = User(email='repair_test2@example.com')
        user.set_password('testpass')
        db.session.add(user)
        db.session.commit()
        
        profile = VoiceProfile(
            user_id=user.id,
            business_name='Test Business'
        )
        
        # Set valid data
        profile.set_platforms(['twitter', 'linkedin'])
        profile.set_goals(['growth', 'engagement'])
        db.session.add(profile)
        db.session.commit()
        
        # Normalize (should not change anything)
        repaired = profile.normalize_json_fields()
        db.session.commit()
        
        # Should report no repairs
        assert len(repaired) == 0
        
        # Data should be unchanged
        assert profile.get_platforms() == ['twitter', 'linkedin']
        assert profile.get_goals() == ['growth', 'engagement']
    
    def test_batch_repair_multiple_profiles(self, app_context):
        """Test repairing multiple profiles at once."""
        # Create multiple users and profiles
        profiles_to_repair = []
        
        for i in range(3):
            user = User(email=f'batch_test{i}@example.com')
            user.set_password('testpass')
            db.session.add(user)
            db.session.commit()
            
            profile = VoiceProfile(
                user_id=user.id,
                business_name=f'Business {i}'
            )
            
            # Corrupt different fields for each
            if i == 0:
                profile.platforms = '[bad json'
            elif i == 1:
                profile.goals = '{"not": "a list"}'
            else:
                profile.customers = 'invalid'
            
            db.session.add(profile)
            profiles_to_repair.append(profile)
        
        db.session.commit()
        
        # Repair all profiles
        total_repairs = 0
        for profile in profiles_to_repair:
            repaired = profile.normalize_json_fields()
            total_repairs += len(repaired)
        
        db.session.commit()
        
        # Should have repaired 3 fields total (one per profile)
        assert total_repairs == 3
        
        # Verify all are now valid
        for profile in profiles_to_repair:
            assert profile.get_platforms() == [] or isinstance(profile.get_platforms(), list)
            assert profile.get_goals() == [] or isinstance(profile.get_goals(), list)
            assert profile.get_customers() == [] or isinstance(profile.get_customers(), list)
