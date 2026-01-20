"""History API routes for content history and usage tracking.

This module provides endpoints for:
- Retrieving user content history with pagination and filtering
- Starring/favoriting content
- Soft-deleting history items
- Reusing previously generated content
- Checking usage limits and stats
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import ContentHistory, db
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
history_bp = Blueprint('history', __name__)


@history_bp.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """Get user's content history with pagination.
    
    Query Parameters:
        page (int): Page number (default: 1)
        per_page (int): Items per page (default: 20, max: 100)
        starred (bool): Filter to starred items only
        task_type (str): Filter by task type
    
    Returns:
        JSON response with paginated history items
    """
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    starred_only = request.args.get('starred', 'false').lower() == 'true'
    task_type = request.args.get('task_type')
    
    # Check tier limits for history access
    tier_limits = current_user.get_tier_limits()
    history_days = tier_limits.get('history_days', 0)
    
    if history_days == 0:
        return jsonify({
            'items': [],
            'total': 0,
            'message': 'Content history is available on Pro and Team plans.',
            'upgrade_required': True
        })
    
    # Build query
    query = ContentHistory.query.filter_by(
        user_id=current_user.id,
    ).filter(ContentHistory.deleted_at.is_(None))
    
    # Apply history window based on tier
    if history_days > 0:
        cutoff = datetime.utcnow() - timedelta(days=history_days)
        query = query.filter(ContentHistory.created_at >= cutoff)
    
    if starred_only:
        query = query.filter(ContentHistory.starred == True)
    
    if task_type:
        query = query.filter(ContentHistory.task_type == task_type)
    
    # Order and paginate
    query = query.order_by(ContentHistory.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'items': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page,
        'has_next': pagination.has_next,
        'has_prev': pagination.has_prev
    })


@history_bp.route('/api/history/<int:id>', methods=['GET'])
@login_required
def get_history_item(id):
    """Get a specific history item.
    
    Args:
        id: History item ID
    
    Returns:
        JSON response with history item details
    """
    item = ContentHistory.query.filter_by(
        id=id,
        user_id=current_user.id
    ).filter(ContentHistory.deleted_at.is_(None)).first_or_404()
    
    return jsonify(item.to_dict())


@history_bp.route('/api/history/<int:id>/star', methods=['POST'])
@login_required
def toggle_star(id):
    """Toggle star status on a history item.
    
    Args:
        id: History item ID
    
    Returns:
        JSON response with new star status
    """
    item = ContentHistory.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    item.starred = not item.starred
    db.session.commit()
    
    return jsonify({'starred': item.starred})


@history_bp.route('/api/history/<int:id>', methods=['DELETE'])
@login_required
def delete_history_item(id):
    """Soft delete a history item.
    
    Args:
        id: History item ID
    
    Returns:
        JSON response confirming deletion
    """
    item = ContentHistory.query.filter_by(
        id=id,
        user_id=current_user.id
    ).first_or_404()
    
    item.deleted_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'deleted': True})


@history_bp.route('/api/history/<int:id>/reuse', methods=['POST'])
@login_required
def reuse_content(id):
    """Get content for reuse (copy or regenerate variant).
    
    Args:
        id: History item ID
    
    Returns:
        JSON response with content details for reuse
    """
    item = ContentHistory.query.filter_by(
        id=id,
        user_id=current_user.id
    ).filter(ContentHistory.deleted_at.is_(None)).first_or_404()
    
    return jsonify({
        'content': item.generated_content,
        'task_type': item.task_type,
        'platform': item.platform,
        'topic': item.topic,
        'parameters': item.parameters
    })


@history_bp.route('/api/usage', methods=['GET'])
@login_required
def get_usage():
    """Get current usage stats for the user.
    
    Returns:
        JSON response with usage statistics and tier limits
    """
    tier_limits = current_user.get_tier_limits()
    
    return jsonify({
        'tier': current_user.subscription_tier,
        'generations_used': current_user.generation_count_month or 0,
        'generations_limit': tier_limits['generations'],
        'generations_remaining': current_user.generations_remaining(),
        'profiles_limit': tier_limits['profiles'],
        'history_days': tier_limits['history_days'],
        'reset_date': current_user.generation_reset_date.isoformat() if current_user.generation_reset_date else None
    })
