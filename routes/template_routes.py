"""Template API routes for Content Templates Library.

Provides endpoints for:
- Listing all templates (with optional filters)
- Getting a specific template by ID
- Getting recommended templates based on user's profile
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services.template_service import (
    get_all_templates,
    get_template_by_id,
    get_templates_by_industry,
    get_templates_by_task_type,
    get_recommended_templates,
    search_templates
)
from models import VoiceProfile, db
import logging

logger = logging.getLogger(__name__)

template_bp = Blueprint('templates', __name__)


@template_bp.route('/api/templates', methods=['GET'])
@login_required
def list_templates():
    """List all templates with optional filtering.
    
    Query Parameters:
        industry: Filter by industry (e.g., 'restaurant', 'fitness')
        task_type: Filter by task type (e.g., 'post', 'email', 'script')
        search: Search query for name/description
    
    Returns:
        JSON response with templates array
    """
    try:
        # Get query parameters
        industry_filter = request.args.get('industry')
        task_type_filter = request.args.get('task_type')
        search_query = request.args.get('search')
        
        # Apply filters
        if search_query:
            templates = search_templates(search_query)
        elif industry_filter and task_type_filter:
            templates = get_recommended_templates(industry_filter, task_type_filter)
        elif industry_filter:
            templates = get_templates_by_industry(industry_filter)
        elif task_type_filter:
            templates = get_templates_by_task_type(task_type_filter)
        else:
            templates = get_all_templates()
        
        # Convert to dict format
        templates_data = [t.to_dict() for t in templates]
        
        logger.info(f"Listed {len(templates_data)} templates for user {current_user.id} with filters: industry={industry_filter}, task_type={task_type_filter}, search={search_query}")
        
        return jsonify({
            'templates': templates_data,
            'count': len(templates_data)
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing templates: {e}")
        return jsonify({'error': 'Failed to list templates'}), 500


@template_bp.route('/api/templates/<template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """Get a specific template by ID.
    
    Args:
        template_id: The template ID
    
    Returns:
        JSON response with template data
    """
    try:
        template = get_template_by_id(template_id)
        
        if not template:
            return jsonify({'error': 'Template not found'}), 404
        
        logger.info(f"Retrieved template {template_id} for user {current_user.id}")
        
        return jsonify({
            'template': template.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting template {template_id}: {e}")
        return jsonify({'error': 'Failed to get template'}), 500


@template_bp.route('/api/templates/recommended', methods=['GET'])
@login_required
def get_recommended():
    """Get recommended templates based on user's profile.
    
    Uses the user's industry from their voice profile to recommend
    relevant templates. Falls back to general templates if no profile exists.
    
    Query Parameters:
        task_type: Optional task type filter
    
    Returns:
        JSON response with recommended templates
    """
    try:
        # Get user's profile to determine industry
        profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
        
        industry = None
        if profile and profile.industry:
            # Normalize industry names
            industry = profile.industry.lower().strip()
        
        # Get task type filter if provided
        task_type_filter = request.args.get('task_type')
        
        # Get recommended templates
        templates = get_recommended_templates(industry, task_type_filter)
        
        # Convert to dict format
        templates_data = [t.to_dict() for t in templates]
        
        logger.info(f"Recommended {len(templates_data)} templates for user {current_user.id} (industry={industry}, task_type={task_type_filter})")
        
        return jsonify({
            'templates': templates_data,
            'count': len(templates_data),
            'industry': industry
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting recommended templates: {e}")
        return jsonify({'error': 'Failed to get recommended templates'}), 500
