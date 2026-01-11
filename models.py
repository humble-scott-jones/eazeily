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
