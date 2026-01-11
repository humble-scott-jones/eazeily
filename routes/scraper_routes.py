"""Scraping routes for extracting business information from URLs."""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, VoiceProfile
from services.scraper_service import scrape_url, extract_business_info
import logging
import uuid
import threading
import os
from datetime import datetime

scraper_bp = Blueprint('scraper', __name__)
logger = logging.getLogger(__name__)

# In-memory job storage (for simplicity; could be Redis or DB for production)
scrape_jobs = {}
jobs_lock = threading.Lock()


def _get_outbound_kill_switch():
    """Get the current state of the outbound kill switch from environment."""
    return os.getenv('OUTBOUND_KILL_SWITCH', 'false').lower() == 'true'


def _validate_url(url: str) -> tuple[bool, str]:
    """Validate URL format and accessibility.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL is required"
    
    url = url.strip()
    if not url:
        return False, "URL cannot be empty"
    
    # Basic URL validation
    if not (url.startswith('http://') or url.startswith('https://')):
        return False, "URL must start with http:// or https://"
    
    # Check for minimum length
    if len(url) < 10:
        return False, "URL seems invalid"
    
    return True, ""


def _run_scrape_job(job_id: str, url: str, profile_id: int, app):
    """Background worker to scrape URL and update profile.
    
    This function runs in a separate thread and:
    1. Fetches and parses the URL
    2. Extracts business information
    3. Updates the profile with scraped data
    4. Updates job status
    
    Args:
        job_id: Unique job identifier
        url: URL to scrape
        profile_id: Profile database ID
        app: Flask app instance
    """
    with app.app_context():
        try:
            logger.info(f"Starting scrape job {job_id} for URL: {url}")
            
            # Update job status to running
            with jobs_lock:
                if job_id in scrape_jobs:
                    scrape_jobs[job_id]['status'] = 'running'
                    scrape_jobs[job_id]['started_at'] = datetime.utcnow().isoformat()
            
            # Step 1: Scrape the URL
            scraped_text = scrape_url(url, max_length=5000)
            
            if not scraped_text:
                raise Exception("Failed to extract text from URL")
            
            # Step 2: Extract business information using AI
            business_info = extract_business_info(scraped_text, url)
            
            # Step 3: Prepare structured metadata
            scraped_meta = {
                'url': url,
                'extracted_at': datetime.utcnow().isoformat(),
                'text_length': len(scraped_text),
                'business_name': business_info.get('business_name'),
                'industry': business_info.get('industry'),
                'key_customers': business_info.get('key_customers'),
                'brand_keywords': business_info.get('brand_keywords', []),
                'niche_keywords': business_info.get('niche_keywords', [])
            }
            
            # Step 4: Update profile in database
            profile = VoiceProfile.query.get(profile_id)
            if profile:
                profile.scraped_url = url
                profile.set_scraped_meta(scraped_meta)
                profile.scraped_at = datetime.utcnow()
                profile.scrape_status = 'finished'
                
                # Update profile fields if they're empty
                if business_info.get('business_name') and not profile.business_name:
                    profile.business_name = business_info.get('business_name')
                
                if business_info.get('industry') and not profile.industry:
                    profile.industry = business_info.get('industry')
                
                if business_info.get('key_customers') and not profile.target_audience:
                    profile.target_audience = business_info.get('key_customers')
                
                # Merge keywords if we have AI-extracted ones
                existing_brand_keywords = profile.get_brand_keywords()
                if business_info.get('brand_keywords'):
                    new_keywords = list(set(existing_brand_keywords + business_info['brand_keywords']))
                    profile.set_brand_keywords(new_keywords)
                
                existing_niche_keywords = profile.get_niche_keywords()
                if business_info.get('niche_keywords'):
                    new_keywords = list(set(existing_niche_keywords + business_info['niche_keywords']))
                    profile.set_niche_keywords(new_keywords)
                
                db.session.commit()
                logger.info(f"Scrape job {job_id} completed successfully")
            
            # Step 5: Update job with success result
            with jobs_lock:
                if job_id in scrape_jobs:
                    scrape_jobs[job_id]['status'] = 'finished'
                    scrape_jobs[job_id]['finished_at'] = datetime.utcnow().isoformat()
                    scrape_jobs[job_id]['result'] = {
                        'ok': True,
                        'company': business_info.get('business_name'),
                        'industry': business_info.get('industry'),
                        'key_customers': business_info.get('key_customers'),
                        'brand_keywords': business_info.get('brand_keywords', []),
                        'niche_keywords': business_info.get('niche_keywords', []),
                        'scraped_meta': scraped_meta
                    }
        
        except Exception as e:
            logger.error(f"Scrape job {job_id} failed: {e}", exc_info=True)
            
            # Update profile with failed status
            try:
                profile = VoiceProfile.query.get(profile_id)
                if profile:
                    profile.scrape_status = 'failed'
                    profile.scraped_at = datetime.utcnow()
                    db.session.commit()
            except Exception as db_error:
                logger.error(f"Failed to update profile after scrape error: {db_error}")
            
            # Update job with error
            with jobs_lock:
                if job_id in scrape_jobs:
                    scrape_jobs[job_id]['status'] = 'failed'
                    scrape_jobs[job_id]['finished_at'] = datetime.utcnow().isoformat()
                    scrape_jobs[job_id]['result'] = {
                        'ok': False,
                        'error': str(e)
                    }


@scraper_bp.route('/api/scrape', methods=['POST'])
@login_required
def api_scrape():
    """Start a URL scraping job.
    
    POST /api/scrape
    Body: { "url": "https://example.com" }
    
    Returns:
        { "ok": true, "job_id": "...", "message": "..." }
    """
    request_id = str(uuid.uuid4())
    
    try:
        # Check kill switch
        if _get_outbound_kill_switch():
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': {
                    'code': 'service_disabled',
                    'message': 'URL scraping is currently disabled'
                }
            }), 503
        
        data = request.get_json() or {}
        url = data.get('url', '').strip()
        
        # Validate URL
        is_valid, error_msg = _validate_url(url)
        if not is_valid:
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': {
                    'code': 'invalid_url',
                    'message': error_msg
                }
            }), 400
        
        # Get or create profile for user
        profile = VoiceProfile.query.filter_by(user_id=current_user.id).first()
        if not profile:
            logger.info(f"Creating new profile for user {current_user.id} during scrape")
            profile = VoiceProfile(user_id=current_user.id)
            db.session.add(profile)
            db.session.flush()  # Get ID without committing
        
        # Update profile with pending status
        profile.scrape_status = 'pending'
        profile.scraped_url = url
        db.session.commit()
        
        # Create job
        job_id = str(uuid.uuid4())
        with jobs_lock:
            scrape_jobs[job_id] = {
                'id': job_id,
                'profile_id': profile.id,
                'url': url,
                'status': 'pending',
                'created_at': datetime.utcnow().isoformat(),
                'started_at': None,
                'finished_at': None,
                'result': None
            }
        
        # Start background thread
        # Pass the app instance to the thread (not current_app proxy)
        from flask import current_app
        app_instance = current_app._get_current_object()
        
        thread = threading.Thread(
            target=_run_scrape_job,
            args=(job_id, url, profile.id, app_instance),
            daemon=True
        )
        thread.start()
        
        logger.info(f"Started scrape job {job_id} for user {current_user.id}")
        
        return jsonify({
            'ok': True,
            'request_id': request_id,
            'job_id': job_id,
            'message': 'Scraping started'
        }), 200
    
    except Exception as e:
        logger.error(f"Error starting scrape job: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({
            'ok': False,
            'request_id': request_id,
            'error': {
                'code': 'scrape_error',
                'message': f'Failed to start scraping: {str(e)}'
            }
        }), 500


@scraper_bp.route('/api/scrape-job/<job_id>', methods=['GET'])
@login_required
def api_scrape_job(job_id: str):
    """Get the status of a scraping job.
    
    GET /api/scrape-job/<job_id>
    
    Returns:
        { "ok": true, "job": { "status": "...", "result": {...} } }
    """
    request_id = str(uuid.uuid4())
    
    try:
        with jobs_lock:
            job = scrape_jobs.get(job_id)
        
        if not job:
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': {
                    'code': 'job_not_found',
                    'message': 'Scraping job not found'
                }
            }), 404
        
        # Verify the job belongs to the current user's profile
        profile = VoiceProfile.query.get(job['profile_id'])
        if not profile or profile.user_id != current_user.id:
            return jsonify({
                'ok': False,
                'request_id': request_id,
                'error': {
                    'code': 'unauthorized',
                    'message': 'You do not have access to this job'
                }
            }), 403
        
        return jsonify({
            'ok': True,
            'request_id': request_id,
            'job': {
                'id': job['id'],
                'status': job['status'],
                'created_at': job['created_at'],
                'started_at': job['started_at'],
                'finished_at': job['finished_at'],
                'result': job['result']
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching scrape job {job_id}: {e}", exc_info=True)
        return jsonify({
            'ok': False,
            'request_id': request_id,
            'error': {
                'code': 'job_fetch_error',
                'message': f'Failed to fetch job status: {str(e)}'
            }
        }), 500
