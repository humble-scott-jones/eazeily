from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, VoiceProfile
import logging
import uuid

profile_bp = Blueprint('profile', __name__)
logger = logging.getLogger(__name__)


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
                        'include_images': False
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
                'include_images': profile.include_images or False
            }
            
            return jsonify({
                'ok': True,
                'request_id': request_id,
                'profile_status': 'loaded',
                'profile': profile_data
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
                profile.target_audience = data['target_audience']
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
            'include_images': profile.include_images or False
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
