from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from models import db, VoiceProfile
import logging
import uuid
from services.profile_expert import generate_profile_suggestions, process_raw_audience_input
from services.profile_validator import get_profile_completeness

profile_bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)

# Constants for target audience AI processing
AUDIENCE_AI_LENGTH_THRESHOLD = 100
AUDIENCE_AI_KEYWORDS = ['website', 'look at', 'look on', 'analyze', 'come up with', 'check my', 'http://', 'https://']


@profile_bp.route('/profile')
@login_required
def profile_page():
    """Render the standalone editable profile page."""
    return render_template('profile.html')


def _coerce_str_list(val):
    """Helper to coerce input to a list of strings."""
    if val is None:
        return []
    if isinstance(val, list):
        return [str(item) for item in val]
    if isinstance(val, str):
        # If it's a single string, treat it as one item
        return [val] if val.strip() else []
    return []


@profile_bp.route('/api/profile', methods=['GET', 'POST'])
@login_required
def api_profile():
    """
    GET: Retrieve the user's brand profile
    POST: Save/update the user's brand profile
    
    This endpoint handles the brand profile data including:
    - Basic info (company/business_name, industry, tone/brand_voice)
    - Keywords (brand_keywords, niche_keywords)
    - Target audience and key offer
    - Brand inspirations and anti-inspirations
    - Platform preferences
    - Voice rules and writing samples
    """
    request_id = str(uuid.uuid4())
    
    if request.method == 'GET':
        try:
            profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
            
            if not profile:
                # Return default empty profile
                return jsonify({
                    'ok': True,
                    'request_id': request_id,
                    'profile_status': 'empty',
                    'profile': {
                        'company': '',
                        'industry': '',
                        'tone': '',
                        'platforms': [],
                        'timezone': '',
                        'brand_keywords': [],
                        'niche_keywords': [],
                        'goals': [],
                        'target_audience': '',
                        'brand_voice': '',
                        'key_offer': '',
                        'voice_rules': '',
                        'writing_samples': [],
                        'brand_inspirations': [],
                        'brand_anti_inspirations': [],
                        'vibe_preset': None,
                        'include_images': False,
                        # Scraper fields
                        'customers': [],
                        'scraped_url': '',
                        'scraped_meta': {},
                        'scraped_at': None,
                        'scrape_status': 'none'
                    },
                    'completeness': {
                        'percent': 0,
                        'is_complete': False,
                        'missing_fields': ['Business Name', 'Industry', 'Brand Voice', 'Target Audience', 'Key Offer', 'Writing Samples', 'Brand Keywords', 'Goals'],
                        'field_status': {
                            'business_name': False,
                            'industry': False,
                            'brand_voice': False,
                            'target_audience': False,
                            'key_offer': False,
                            'writing_samples': False,
                            'brand_keywords': False,
                            'goals': False
                        }
                    }
                }), 200
            
            # Build profile response
            profile_data = {
                'id': profile.id,
                'company': profile.business_name or '',
                'industry': profile.industry or '',
                'tone': profile.tone or profile.brand_voice or '',
                'platforms': profile.get_platforms(),
                'timezone': profile.timezone or '',
                'brand_keywords': profile.get_brand_keywords(),
                'niche_keywords': profile.get_niche_keywords(),
                'goals': profile.get_goals(),
                'target_audience': profile.target_audience or '',
                'brand_voice': profile.brand_voice or '',
                'key_offer': profile.key_offer or '',
                'voice_rules': profile.voice_rules or '',
                'writing_samples': profile.get_writing_samples(),
                'brand_inspirations': profile.get_brand_inspirations(),
                'brand_anti_inspirations': profile.get_brand_anti_inspirations(),
                'vibe_preset': profile.vibe_preset,
                'include_images': profile.include_images or False,
                # Scraper fields
                'customers': profile.get_customers(),
                'scraped_url': profile.scraped_url or '',
                'scraped_meta': profile.get_scraped_meta(),
                'scraped_at': profile.scraped_at.isoformat() if profile.scraped_at else None,
                'scrape_status': profile.scrape_status or 'none'
            }
            
            # Calculate profile completeness using the validator service
            is_complete, missing_fields, completeness_percent = get_profile_completeness(profile)
            
            # Build field status for client-side UI
            field_status = {
                'business_name': bool(profile.business_name and profile.business_name.strip()),
                'industry': bool(profile.industry and profile.industry.strip()),
                'brand_voice': bool(profile.brand_voice and profile.brand_voice.strip()),
                'target_audience': bool(profile.target_audience and profile.target_audience.strip()),
                'key_offer': bool(profile.key_offer and profile.key_offer.strip()),
                'writing_samples': bool(profile.get_writing_samples()),
                'brand_keywords': bool(profile.get_brand_keywords()),
                'goals': bool(profile.get_goals())
            }
            
            return jsonify({
                'ok': True,
                'request_id': request_id,
                'profile_status': 'loaded',
                'profile': profile_data,
                'completeness': {
                    'percent': completeness_percent,
                    'is_complete': is_complete,
                    'missing_fields': missing_fields,
                    'field_status': field_status
                }
            }), 200
            
        except Exception as e:
            logger.error(f"Error loading profile for user {current_user.id}: {e}", exc_info=True)
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': {
                    'code': 'profile_load_error',
                    'message': 'Failed to load profile'
                }
            }), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json() or {}
            
            # Get or create profile
            profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
            if not profile:
                logger.info(f"Creating new VoiceProfile for user {current_user.id}")
                profile = VoiceProfile(user_id=current_user.id)
                db.session.add(profile)
            else:
                logger.info(f"Updating existing VoiceProfile (id={profile.id}) for user {current_user.id}")
            
            # Update basic fields
            # Map 'company' to business_name for compatibility
            if 'company' in data:
                profile.business_name = data['company']
            elif 'business_name' in data:
                profile.business_name = data['business_name']
            
            if 'industry' in data:
                profile.industry = data['industry']
            
            # Map 'tone' to both tone and brand_voice fields
            if 'tone' in data:
                profile.tone = data['tone']
                # If brand_voice is not explicitly set, use tone
                if 'brand_voice' not in data and data['tone']:
                    profile.brand_voice = data['tone']
            
            if 'brand_voice' in data:
                profile.brand_voice = data['brand_voice']
            
            if 'timezone' in data:
                profile.timezone = data['timezone']
            
            if 'target_audience' in data:
                raw_input = data['target_audience']
                
                # If input looks like a prompt/request, process through AI
                if raw_input and (len(raw_input) > AUDIENCE_AI_LENGTH_THRESHOLD or any(word in raw_input.lower() for word in AUDIENCE_AI_KEYWORDS)):
                    logger.info(f"Target audience appears to be a prompt/request, processing through AI")
                    processed = process_raw_audience_input(raw_input, profile)
                    if processed['success']:
                        profile.target_audience = processed['audience']
                        logger.info(f"Successfully processed target audience: '{raw_input[:50]}...' -> '{processed['audience'][:50]}...'")
                    else:
                        # Fallback: store as-is but log warning
                        logger.warning(f"Failed to process target audience: {processed.get('error')}")
                        profile.target_audience = raw_input
                else:
                    # Short, direct input - store as-is
                    profile.target_audience = raw_input
            elif 'key_customers' in data:
                # Map key_customers to target_audience
                profile.target_audience = data['key_customers']
            
            if 'key_offer' in data:
                profile.key_offer = data['key_offer']
            
            if 'voice_rules' in data:
                profile.voice_rules = data['voice_rules']
            
            if 'vibe_preset' in data:
                profile.vibe_preset = data['vibe_preset']
            
            if 'include_images' in data:
                profile.include_images = bool(data['include_images'])
            
            # Update list fields
            if 'platforms' in data:
                profile.set_platforms(_coerce_str_list(data['platforms']))
            
            if 'brand_keywords' in data:
                profile.set_brand_keywords(_coerce_str_list(data['brand_keywords']))
            
            if 'niche_keywords' in data:
                profile.set_niche_keywords(_coerce_str_list(data['niche_keywords']))
            
            if 'goals' in data:
                profile.set_goals(_coerce_str_list(data['goals']))
            
            if 'writing_samples' in data:
                profile.set_writing_samples(_coerce_str_list(data['writing_samples']))
            
            # Update brand inspirations (list of objects)
            if 'brand_inspirations' in data:
                inspirations = data['brand_inspirations']
                if isinstance(inspirations, list):
                    profile.set_brand_inspirations(inspirations)
            
            if 'brand_anti_inspirations' in data:
                anti_inspirations = data['brand_anti_inspirations']
                if isinstance(anti_inspirations, list):
                    profile.set_brand_anti_inspirations(anti_inspirations)
            
            # Update scraper-related fields
            if 'customers' in data:
                customers = data['customers']
                if isinstance(customers, list):
                    profile.set_customers(customers)
                elif isinstance(customers, str):
                    # If sent as a string, try to parse or treat as single item
                    profile.set_customers([customers] if customers.strip() else [])
            
            if 'scraped_url' in data:
                profile.scraped_url = data['scraped_url']
            
            if 'scraped_meta' in data:
                meta = data['scraped_meta']
                if isinstance(meta, dict):
                    profile.set_scraped_meta(meta)
                elif isinstance(meta, str):
                    # If sent as JSON string, store directly
                    profile.scraped_meta = meta
            
            if 'scraped_at' in data:
                from datetime import datetime
                scraped_at_val = data['scraped_at']
                if scraped_at_val:
                    if isinstance(scraped_at_val, str):
                        profile.scraped_at = datetime.fromisoformat(scraped_at_val.replace('Z', '+00:00'))
                    else:
                        profile.scraped_at = scraped_at_val
            
            if 'scrape_status' in data:
                profile.scrape_status = data['scrape_status']
            
            # Commit changes
            db.session.commit()
            
            logger.info(f"Profile saved successfully for user {current_user.id}, profile_id={profile.id}")
            
            return jsonify({
                'ok': True,
                'request_id': request_id,
                'id': profile.id,
                'message': 'Profile saved successfully'
            }), 200
            
        except Exception as e:
            logger.error(f"Error saving profile for user {current_user.id}: {e}", exc_info=True)
            db.session.rollback()
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': {
                    'code': 'profile_save_error',
                    'message': f'Failed to save profile: {str(e)}'
                }
            }), 500


@profile_bp.route('/api/profile_v2', methods=['GET'])
@login_required
def api_profile_v2():
    """
    Alternative profile endpoint that returns profile data in a slightly different format.
    Used by the generate page for profile hydration.
    """
    request_id = str(uuid.uuid4())
    
    try:
        profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
        
        if not profile:
            return jsonify({
                'ok': True,
                'request_id': request_id,
                'profile_status': 'empty',
                'profile': None
            }), 200
        
        # Build profile response similar to v1 but with all fields
        profile_data = {
            'id': profile.id,
            'company': profile.business_name or '',
            'business_name': profile.business_name or '',
            'industry': profile.industry or '',
            'tone': profile.tone or profile.brand_voice or '',
            'brand_voice': profile.brand_voice or '',
            'platforms': profile.get_platforms(),
            'timezone': profile.timezone or '',
            'brand_keywords': profile.get_brand_keywords(),
            'niche_keywords': profile.get_niche_keywords(),
            'goals': profile.get_goals(),
            'target_audience': profile.target_audience or '',
            'key_offer': profile.key_offer or '',
            'voice_rules': profile.voice_rules or '',
            'writing_samples': profile.get_writing_samples(),
            'brand_inspirations': profile.get_brand_inspirations(),
            'brand_anti_inspirations': profile.get_brand_anti_inspirations(),
            'vibe_preset': profile.vibe_preset,
            'include_images': profile.include_images or False,
            # Scraper fields
            'customers': profile.get_customers(),
            'scraped_url': profile.scraped_url or '',
            'scraped_meta': profile.get_scraped_meta(),
            'scraped_at': profile.scraped_at.isoformat() if profile.scraped_at else None,
            'scrape_status': profile.scrape_status or 'none'
        }
        
        return jsonify({
            'ok': True,
            'request_id': request_id,
            'profile_status': 'loaded',
            'profile': profile_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error loading profile_v2 for user {current_user.id}: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'request_id': request_id,
            'error': {
                'code': 'profile_load_error',
                'message': 'Failed to load profile'
            }
        }), 500


# Alias for /api/signup to /auth/signup for test compatibility
@profile_bp.route('/api/signup', methods=['POST'])
def api_signup():
    """Alias route that forwards to /auth/signup for API compatibility."""
    from routes.auth_routes import signup
    return signup()


@profile_bp.route('/api/current_user', methods=['GET'])
@login_required
def api_current_user():
    """Get current user and their profile information."""
    try:
        profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
        
        user_data = {
            'id': current_user.id,
            'email': current_user.email
        }
        
        profile_data = None
        if profile:
            profile_data = {
                'id': profile.id,
                'business_name': profile.business_name or '',
                'industry': profile.industry or '',
                'brand_voice': profile.brand_voice or '',
                'target_audience': profile.target_audience or '',
                'key_offer': profile.key_offer or ''
            }
        
        return jsonify({
            'ok': True,
            'user': user_data,
            'profile': profile_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'error': {
                'code': 'current_user_error',
                'message': 'Failed to get current user'
            }
        }), 500


@profile_bp.route('/api/profile/suggest', methods=['POST'])
@login_required
def suggest_profile_field():
    """Generate AI-powered suggestions for a profile field using Gemini."""
    
    data = request.get_json()
    field = data.get('field')
    
    if not field:
        return jsonify({
            'success': False,
            'error': 'Field is required'
        }), 400
    
    valid_fields = ['target_audience', 'brand_voice', 'key_offer', 'writing_samples', 'voice_rules']
    if field not in valid_fields:
        return jsonify({
            'success': False,
            'error': f'Invalid field. Must be one of: {", ".join(valid_fields)}'
        }), 400
    
    # Get user's current profile
    profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        return jsonify({
            'success': False,
            'error': 'No profile found. Please create a profile first.'
        }), 404
    
    # Convert profile to dict for the service
    profile_dict = {
        'company': profile.business_name,
        'business_name': profile.business_name,
        'industry': profile.industry,
        'tone': profile.brand_voice,
        'brand_voice': profile.brand_voice,
        'target_audience': profile.target_audience,
        'key_offer': profile.key_offer,
        'voice_rules': profile.voice_rules,
        'writing_samples': profile.get_writing_samples(),
    }
    
    result = generate_profile_suggestions(field, profile_dict)
    
    return jsonify(result)


# =============================================================================
# Multi-Profile Management Endpoints
# =============================================================================

@profile_bp.route('/api/profiles', methods=['GET'])
@login_required
def list_profiles():
    """List all profiles for the current user.
    
    Returns:
        JSON array of profile objects with basic info
    """
    request_id = str(uuid.uuid4())
    
    try:
        profiles = VoiceProfile.query.filter_by(user_id=current_user.id).all()
        
        profile_list = []
        for profile in profiles:
            profile_list.append({
                'id': profile.id,
                'profile_name': profile.profile_name,
                'business_name': profile.business_name,
                'industry': profile.industry,
                'is_default': profile.is_default,
            })
        
        return jsonify({
            'ok': True,
            'request_id': request_id,
            'profiles': profile_list,
            'count': len(profile_list),
            'tier_limit': current_user.get_tier_limits()['profiles'],
            'can_create_more': current_user.can_create_profile()
        })
        
    except Exception as e:
        logger.error(f"Error listing profiles: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'request_id': request_id,
            'error': 'Failed to list profiles'
        }), 500


@profile_bp.route('/api/profiles', methods=['POST'])
@login_required
def create_profile():
    """Create a new profile for the current user.
    
    Enforces tier limits on number of profiles.
    
    Request body:
        {
            "profile_name": "Client: Acme Co",
            "business_name": "Acme Corporation",
            "industry": "Technology",
            ... other profile fields
        }
    
    Returns:
        JSON with new profile info or error
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Check if user can create more profiles
        if not current_user.can_create_profile():
            tier_limit = current_user.get_tier_limits()['profiles']
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': f'Profile limit reached for {current_user.subscription_tier} tier. Maximum: {tier_limit}'
            }), 403
        
        data = request.get_json()
        
        # Create new profile
        profile = VoiceProfile(user_id=current_user.id)
        
        # Set profile_name (required for multi-profile)
        profile.profile_name = data.get('profile_name', data.get('business_name', 'New Profile'))
        
        # Set is_default if this is the first profile
        profile_count = VoiceProfile.query.filter_by(user_id=current_user.id).count()
        profile.is_default = (profile_count == 0)
        
        # Set other fields from request
        if 'business_name' in data:
            profile.business_name = data['business_name']
        if 'industry' in data:
            profile.industry = data['industry']
        if 'target_audience' in data:
            profile.target_audience = data['target_audience']
        if 'brand_voice' in data:
            profile.brand_voice = data['brand_voice']
        if 'key_offer' in data:
            profile.key_offer = data['key_offer']
        if 'voice_rules' in data:
            profile.voice_rules = data['voice_rules']
        if 'writing_samples' in data:
            profile.set_writing_samples(_coerce_str_list(data['writing_samples']))
        if 'brand_keywords' in data:
            profile.set_brand_keywords(_coerce_str_list(data['brand_keywords']))
        if 'goals' in data:
            profile.set_goals(_coerce_str_list(data['goals']))
        
        db.session.add(profile)
        db.session.commit()
        
        logger.info(f"Created new profile {profile.id} for user {current_user.id}")
        
        return jsonify({
            'ok': True,
            'request_id': request_id,
            'profile': {
                'id': profile.id,
                'profile_name': profile.profile_name,
                'business_name': profile.business_name,
                'industry': profile.industry,
                'is_default': profile.is_default,
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating profile: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'ok': False,
            'request_id': request_id,
            'error': 'Failed to create profile'
        }), 500


@profile_bp.route('/api/profiles/<int:profile_id>/default', methods=['PUT'])
@login_required
def set_default_profile(profile_id):
    """Set a profile as the default profile.
    
    Args:
        profile_id: ID of the profile to set as default
    
    Returns:
        JSON with success status
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Get the profile and verify ownership
        profile = VoiceProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
        
        if not profile:
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': 'Profile not found'
            }), 404
        
        # Unset all other defaults for this user
        VoiceProfile.query.filter_by(user_id=current_user.id).update({'is_default': False})
        
        # Set this profile as default
        profile.is_default = True
        db.session.commit()
        
        logger.info(f"Set profile {profile_id} as default for user {current_user.id}")
        
        return jsonify({
            'ok': True,
            'request_id': request_id,
            'message': 'Default profile updated'
        })
        
    except Exception as e:
        logger.error(f"Error setting default profile: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'ok': False,
            'request_id': request_id,
            'error': 'Failed to set default profile'
        }), 500


@profile_bp.route('/api/profiles/<int:profile_id>', methods=['DELETE'])
@login_required
def delete_profile(profile_id):
    """Delete a profile.
    
    Prevents deletion of the last profile.
    
    Args:
        profile_id: ID of the profile to delete
    
    Returns:
        JSON with success status
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Get the profile and verify ownership
        profile = VoiceProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
        
        if not profile:
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': 'Profile not found'
            }), 404
        
        # Check if this is the last profile
        profile_count = VoiceProfile.query.filter_by(user_id=current_user.id).count()
        if profile_count <= 1:
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': 'Cannot delete your last profile'
            }), 400
        
        # If deleting the default profile, set another as default
        if profile.is_default:
            # Find another profile to set as default
            other_profile = VoiceProfile.query.filter(
                VoiceProfile.user_id == current_user.id,
                VoiceProfile.id != profile_id
            ).first()
            if other_profile:
                other_profile.is_default = True
        
        db.session.delete(profile)
        db.session.commit()
        
        logger.info(f"Deleted profile {profile_id} for user {current_user.id}")
        
        return jsonify({
            'ok': True,
            'request_id': request_id,
            'message': 'Profile deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting profile: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'ok': False,
            'request_id': request_id,
            'error': 'Failed to delete profile'
        }), 500


@profile_bp.route('/api/profiles/current', methods=['GET'])
@login_required
def get_current_profile():
    """Get the current active profile.
    
    Returns the profile from session if set, otherwise the default profile.
    
    Returns:
        JSON with current profile info
    """
    request_id = str(uuid.uuid4())
    
    try:
        from flask import session
        
        # Check if there's an active profile in session
        active_profile_id = session.get('active_profile_id')
        
        if active_profile_id:
            profile = VoiceProfile.query.filter_by(
                id=active_profile_id,
                user_id=current_user.id
            ).first()
            if profile:
                return jsonify({
                    'ok': True,
                    'request_id': request_id,
                    'profile': {
                        'id': profile.id,
                        'profile_name': profile.profile_name,
                        'business_name': profile.business_name,
                        'industry': profile.industry,
                        'is_default': profile.is_default,
                    },
                    'source': 'session'
                })
        
        # Fall back to default profile
        profile = VoiceProfile.query.filter_by(
            user_id=current_user.id,
            is_default=True
        ).first()
        
        if not profile:
            # If no default, get first profile
            profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
        
        if not profile:
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': 'No profile found'
            }), 404
        
        return jsonify({
            'ok': True,
            'request_id': request_id,
            'profile': {
                'id': profile.id,
                'profile_name': profile.profile_name,
                'business_name': profile.business_name,
                'industry': profile.industry,
                'is_default': profile.is_default,
            },
            'source': 'default'
        })
        
    except Exception as e:
        logger.error(f"Error getting current profile: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'request_id': request_id,
            'error': 'Failed to get current profile'
        }), 500
