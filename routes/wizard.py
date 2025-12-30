import os
import tempfile
from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import current_user, login_required

from models import VoiceProfile, User, db
from services.ingestion import ingest_url, ingest_file
from services.voice_engine import VoiceEngine

wizard_bp = Blueprint('wizard', __name__, template_folder='../templates')


@wizard_bp.route('/setup/voice', methods=['GET', 'POST'])
def setup_voice():
    if request.method == 'GET':
        return render_template('wizard_setup.html')

    # POST: accept url or file upload
    url = request.form.get('url')
    uploaded = request.files.get('file')

    content = ''
    if url:
        content = ingest_url(url)
    elif uploaded:
        # save to temp and let ingestion handle it
        fd, path = tempfile.mkstemp(prefix='eazeily-upload-')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(uploaded.read())
            ingestion_result = ingest_file(path)
            # try to use returned text if available
            if isinstance(ingestion_result, dict) and 'text' in ingestion_result:
                content = ingestion_result.get('text') or ''
        finally:
            try:
                os.remove(path)
            except Exception:
                pass

    if not content:
        return jsonify({'ok': False, 'error': 'No content ingested'}), 400

    engine = VoiceEngine()
    analysis = engine.analyze_style(content)

    # associate with current_user when available, otherwise require form user_id
    user = None
    if current_user and getattr(current_user, 'is_authenticated', False):
        user = current_user
    else:
        user_id = request.form.get('user_id')
        if user_id:
            user = User.query.get(user_id)

    if not user:
        return jsonify({'ok': False, 'error': 'No authenticated user and no user_id provided'}), 401

    profile = VoiceProfile(user_id=user.id, bio=(content[:200] + '...'), style_guide=analysis.get('style_guide'), examples=analysis.get('examples'))
    db.session.add(profile)
    db.session.commit()

    return jsonify({'ok': True, 'profile_id': profile.id, 'analysis': analysis})
