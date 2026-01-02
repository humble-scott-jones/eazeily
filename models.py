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
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    voice_profile = db.relationship('VoiceProfile', backref='user', uselist=False)

    @property
    def is_admin(self):
        import os
        admin_emails = [e.strip().lower() for e in os.environ.get('ADMIN_EMAILS', '').split(',') if e.strip()]
        return self.email.lower() in admin_emails


class VoiceProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    industry = db.Column(db.String(100))
    business_name = db.Column(db.String(100))
    defaults = db.Column(db.Text) # Storing JSON as Text
    examples = db.Column(db.Text) # Storing JSON as Text
    
    def set_defaults(self, defaults_dict):
        self.defaults = json.dumps(defaults_dict)

    def get_defaults(self):
        return json.loads(self.defaults) if self.defaults else {}

    def set_examples(self, examples_list):
        self.examples = json.dumps(examples_list)

    def get_examples(self):
        return json.loads(self.examples) if self.examples else []
    
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
