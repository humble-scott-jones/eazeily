from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime
import json

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # CRITICAL: Use Text to ensure hash is never cut off
    password_hash = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    voice_profile = db.relationship('VoiceProfile', backref='user', uselist=False)

    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password matches the stored hash.
        
        Args:
            password: Plain text password to check
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return bcrypt.check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        import os
        admin_emails = [e.strip().lower() for e in os.environ.get('ADMIN_EMAILS', '').split(',') if e.strip()]
        return self.email.lower() in admin_emails


class VoiceProfile(db.Model):
    __tablename__ = 'voice_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    industry = db.Column(db.String(255))
    business_name = db.Column(db.String(255))
    defaults = db.Column(db.Text) # Storing JSON as Text
    examples = db.Column(db.Text) # Storing JSON as Text
    # New "Secret Sauce" fields
    target_audience = db.Column(db.Text)       # The "Who"
    brand_voice = db.Column(db.String(255))    # The "Vibe"
    key_offer = db.Column(db.Text)             # The "Hook"
    voice_rules = db.Column(db.Text)           # The "Constraints" (e.g., "No emojis")
    writing_samples = db.Column(db.Text)       # The "Rhythm" (Few-shot examples) - stored as JSON
    
    def set_defaults(self, defaults_dict):
        self.defaults = json.dumps(defaults_dict)

    def get_defaults(self):
        return json.loads(self.defaults) if self.defaults else {}

    def set_examples(self, examples_list):
        self.examples = json.dumps(examples_list)

    def get_examples(self):
        return json.loads(self.examples) if self.examples else []
    
    def set_writing_samples(self, samples_list):
        """Set writing samples from a list."""
        self.writing_samples = json.dumps(samples_list)
    
    def get_writing_samples(self):
        """Get writing samples as a list."""
        return json.loads(self.writing_samples) if self.writing_samples else []
    
    @property
    def style_guide(self):
        """
        Get style_guide from defaults for compatibility.
        
        Returns the 'style_guide' value from the defaults JSON field.
        This property provides backward compatibility for code that expects
        direct attribute access to style_guide.
        
        Returns:
            str or None: The style guide text if present in defaults, None otherwise.
        """
        defaults = self.get_defaults()
        return defaults.get('style_guide') if defaults else None
