from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)
    tier = db.Column(db.String(20), default='free', nullable=False)

    profiles = db.relationship('VoiceProfile', backref='user', lazy='dynamic')

    def __repr__(self) -> str:  # pragma: no cover - simple repr
        return f"<User {self.email} id={self.id}>"


class VoiceProfile(db.Model):
    __tablename__ = 'voice_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    style_guide = db.Column(db.Text, nullable=True)
    # examples can be stored as JSON when supported by the DB
    examples = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<VoiceProfile id={self.id} user_id={self.user_id}>"
