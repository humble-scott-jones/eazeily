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
    
    # Subscription & Usage Tracking
    subscription_tier = db.Column(db.String(20), default='free')
    generation_count_month = db.Column(db.Integer, default=0)
    generation_reset_date = db.Column(db.DateTime)
    
    # Relationship - support multiple profiles
    voice_profiles = db.relationship('VoiceProfile', backref='user', lazy='dynamic')
    
    # Tier configuration (can be moved to config later)
    TIER_LIMITS = {
        'free': {'generations': 10, 'profiles': 1, 'history_days': 0},
        'pro': {'generations': -1, 'profiles': 3, 'history_days': 30},  # -1 = unlimited
        'team': {'generations': -1, 'profiles': -1, 'history_days': 90},
    }

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
    
    def can_generate(self) -> bool:
        """Check if user can generate content based on tier limits."""
        limits = self.TIER_LIMITS.get(self.subscription_tier, self.TIER_LIMITS['free'])
        if limits['generations'] == -1:
            return True
        
        # Reset counter if new month
        self._reset_generation_counter_if_needed()
        
        return self.generation_count_month < limits['generations']
    
    def _reset_generation_counter_if_needed(self):
        """Reset generation counter if we're in a new month."""
        now = datetime.utcnow()
        if self.generation_reset_date is None or \
           self.generation_reset_date.month != now.month or \
           self.generation_reset_date.year != now.year:
            self.generation_count_month = 0
            self.generation_reset_date = now
            db.session.commit()
    
    def increment_generation(self):
        """Increment the monthly generation counter."""
        self.generation_count_month = (self.generation_count_month or 0) + 1
        db.session.commit()
    
    def generations_remaining(self) -> int:
        """Return remaining generations this month, or -1 for unlimited."""
        limits = self.TIER_LIMITS.get(self.subscription_tier, self.TIER_LIMITS['free'])
        if limits['generations'] == -1:
            return -1
        return max(0, limits['generations'] - (self.generation_count_month or 0))
    
    def get_tier_limits(self) -> dict:
        """Return the limits for the user's current tier."""
        return self.TIER_LIMITS.get(self.subscription_tier, self.TIER_LIMITS['free'])
    
    def can_create_profile(self) -> bool:
        """Check if user can create another profile based on tier limits.
        
        Returns:
            bool: True if user can create another profile, False otherwise
        """
        limits = self.TIER_LIMITS.get(self.subscription_tier, self.TIER_LIMITS['free'])
        max_profiles = limits['profiles']
        
        # -1 means unlimited
        if max_profiles == -1:
            return True
        
        # Count existing profiles
        current_count = VoiceProfile.query.filter_by(user_id=self.id).count()
        return current_count < max_profiles
    
    @property
    def voice_profile(self):
        """Backward compatibility property for single profile access.
        
        Returns the default profile, or first profile if no default is set.
        """
        default_profile = VoiceProfile.query.filter_by(user_id=self.id, is_default=True).first()
        if default_profile:
            return default_profile
        return VoiceProfile.query.filter_by(user_id=self.id).first()


class VoiceProfile(db.Model):
    __tablename__ = 'voice_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Multi-profile support fields
    is_default = db.Column(db.Boolean, default=False, nullable=False, index=True)
    profile_name = db.Column(db.String(100))
    
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
    
    # Additional profile fields for brand profile wizard
    tone = db.Column(db.String(255))           # Tone/vibe (alias for brand_voice in some contexts)
    platforms = db.Column(db.Text)             # List of platforms (stored as JSON)
    timezone = db.Column(db.String(100))       # User timezone
    brand_keywords = db.Column(db.Text)        # Brand keywords (stored as JSON)
    niche_keywords = db.Column(db.Text)        # Niche keywords (stored as JSON)
    goals = db.Column(db.Text)                 # User goals (stored as JSON)
    brand_inspirations = db.Column(db.Text)    # Brand inspirations (stored as JSON)
    brand_anti_inspirations = db.Column(db.Text) # Brand anti-inspirations (stored as JSON)
    vibe_preset = db.Column(db.String(255))    # Selected vibe preset
    include_images = db.Column(db.Boolean, default=False) # Whether to include images
    
    # Scraper-related fields
    scraped_url = db.Column(db.Text)           # URL that was scraped
    scraped_meta = db.Column(db.Text)          # Metadata from scraping (stored as JSON)
    customers = db.Column(db.Text)             # Target customers/audiences (stored as JSON)
    scraped_at = db.Column(db.DateTime)        # When scraping was performed
    scrape_status = db.Column(db.String(50), default='none')  # Status: none, pending, finished, failed
    
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
    
    def set_platforms(self, platforms_list):
        """Set platforms from a list."""
        self.platforms = json.dumps(platforms_list)
    
    def get_platforms(self):
        """Get platforms as a list."""
        return json.loads(self.platforms) if self.platforms else []
    
    def set_brand_keywords(self, keywords_list):
        """Set brand keywords from a list."""
        self.brand_keywords = json.dumps(keywords_list)
    
    def get_brand_keywords(self):
        """Get brand keywords as a list."""
        return json.loads(self.brand_keywords) if self.brand_keywords else []
    
    def set_niche_keywords(self, keywords_list):
        """Set niche keywords from a list."""
        self.niche_keywords = json.dumps(keywords_list)
    
    def get_niche_keywords(self):
        """Get niche keywords as a list."""
        return json.loads(self.niche_keywords) if self.niche_keywords else []
    
    def set_goals(self, goals_list):
        """Set goals from a list."""
        self.goals = json.dumps(goals_list)
    
    def get_goals(self):
        """Get goals as a list."""
        return json.loads(self.goals) if self.goals else []
    
    def set_brand_inspirations(self, inspirations_list):
        """Set brand inspirations from a list."""
        self.brand_inspirations = json.dumps(inspirations_list)
    
    def get_brand_inspirations(self):
        """Get brand inspirations as a list."""
        return json.loads(self.brand_inspirations) if self.brand_inspirations else []
    
    def set_brand_anti_inspirations(self, anti_inspirations_list):
        """Set brand anti-inspirations from a list."""
        self.brand_anti_inspirations = json.dumps(anti_inspirations_list)
    
    def get_brand_anti_inspirations(self):
        """Get brand anti-inspirations as a list."""
        return json.loads(self.brand_anti_inspirations) if self.brand_anti_inspirations else []
    
    def set_customers(self, customers_list):
        """Set customers from a list."""
        self.customers = json.dumps(customers_list)
    
    def get_customers(self):
        """Get customers as a list."""
        return json.loads(self.customers) if self.customers else []
    
    def set_scraped_meta(self, meta_dict):
        """Set scraped metadata from a dict."""
        self.scraped_meta = json.dumps(meta_dict)
    
    def get_scraped_meta(self):
        """Get scraped metadata as a dict."""
        return json.loads(self.scraped_meta) if self.scraped_meta else {}
    
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


class ContentHistory(db.Model):
    """Stores generated content for user history and reuse."""
    __tablename__ = 'content_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('voice_profile.id', ondelete='SET NULL'), nullable=True)
    task_type = db.Column(db.String(50), nullable=False)
    platform = db.Column(db.String(50))
    topic = db.Column(db.Text)
    generated_content = db.Column(db.Text, nullable=False)
    parameters = db.Column(db.JSON)  # Additional params like mood, cta, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    starred = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)  # Soft delete
    
    # Relationships
    user = db.relationship('User', backref=db.backref('content_history', lazy='dynamic'))
    profile = db.relationship('VoiceProfile', backref=db.backref('content_history', lazy='dynamic'))
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'platform': self.platform,
            'topic': self.topic,
            'generated_content': self.generated_content,
            'parameters': self.parameters,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'starred': self.starred,
            'profile_id': self.profile_id,
        }
    
    @classmethod
    def create_from_generation(cls, user_id, profile_id, task_type, content, 
                                platform=None, topic=None, parameters=None):
        """Create a history entry from a generation."""
        entry = cls(
            user_id=user_id,
            profile_id=profile_id,
            task_type=task_type,
            platform=platform,
            topic=topic,
            generated_content=content,
            parameters=parameters
        )
        db.session.add(entry)
        db.session.commit()
        return entry
