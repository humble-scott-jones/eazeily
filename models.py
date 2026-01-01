from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    tier = db.Column(db.String(20), default='free')
    
    # Relationship
    voice_profile = db.relationship('VoiceProfile', backref='user', uselist=False)

class VoiceProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    bio = db.Column(db.Text)
    style_guide = db.Column(db.Text)
    examples = db.Column(db.Text)  # Storing JSON as Text
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_examples(self, examples_list):
        self.examples = json.dumps(examples_list)

    def get_examples(self):
        return json.loads(self.examples) if self.examples else []
