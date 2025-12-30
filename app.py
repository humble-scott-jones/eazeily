"""Minimal Flask app factory scaffold for v2 migration.

This file intentionally provides a small, well-formed create_app factory
that initializes SQLAlchemy and Flask-Login and exposes a few dev
endpoints used by test harnesses. It replaces the previous malformed
contents and is intended as a safe starting point for the Gemini-native
v2 rewrite.
"""

import os
import subprocess
from typing import Optional

from flask import Flask, jsonify, request, session
from flask_cors import CORS
from flask_login import LoginManager

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# Import shared db instance from models so models and DB live in one place
from models import db  # models.py defines `db` and the model classes
login_manager = LoginManager()


def _get_git_sha() -> Optional[str]:
    try:
        sha = os.environ.get('RAILWAY_GIT_COMMIT_SHA') or os.environ.get('GIT_COMMIT_SHA')
        if sha:
            return sha[:7]
        out = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.DEVNULL)
        return out.decode('ascii').strip()
    except Exception:
        return None


def inject_git_sha():
    return dict(git_sha=_get_git_sha())


def create_app(config_object: Optional[str] = None) -> Flask:
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.setdefault('SECRET_KEY', os.getenv('SECRET_KEY', 'dev-secret-change-me'))

    database_url = os.getenv('DATABASE_URL')
    # Railway / Heroku provide DATABASE_URL which may start with postgres://
    if database_url:
        if database_url.startswith('postgres://'):
            # SQLAlchemy / psycopg2 expect postgresql://
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        default_db_path = os.path.join(os.path.dirname(__file__), 'eazeily.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{default_db_path}'

    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)

    if config_object:
        try:
            app.config.from_object(config_object)
        except Exception:
            pass

    # Initialize extensions imported from their modules
    db.init_app(app)
    login_manager.init_app(app)
    CORS(app)

    # Ensure model modules are imported (so SQLAlchemy knows about them)
    try:
        import models  # noqa: F401 - side-effect: registers models with SQLAlchemy
    except Exception:
        pass

    app.context_processor(inject_git_sha)

    @app.get('/__dev__/ping')
    def _dev_ping():
        return 'pong'

    @app.post('/__dev__/create_user')
    def _dev_create_user():
        if os.environ.get('FLASK_ENV') == 'production':
            return jsonify({'ok': False, 'error': 'Not allowed in production'}), 403
        data = request.get_json(silent=True) or {}
        email = data.get('email')
        if not email:
            return jsonify({'ok': False, 'error': 'Email required'}), 400
        user_id = data.get('id') or email
        session['user_id'] = user_id
        session['email'] = email
        return jsonify({'ok': True, 'id': user_id})

    @app.get('/__dev__/queue-test')
    def _dev_queue_test():
        return jsonify({'ok': True, 'queued': False})

    @app.get('/__dev__/routes')
    def _dev_routes():
        routes = []
        try:
            for rule in app.url_map.iter_rules():
                if rule.rule.startswith('/__dev__'):
                    routes.append({'rule': rule.rule})
        except Exception:
            routes = [{'rule': '/__dev__/ping'}, {'rule': '/__dev__/create_user'}, {'rule': '/__dev__/queue-test'}]
        return jsonify({'ok': True, 'routes': routes})

    # Register application blueprints if present
    try:
        from routes import register_blueprints
        register_blueprints(app)
    except Exception:
        # If routes package isn't present yet keep going; this is expected during early boot
        pass

    # Wrap with WhiteNoise for static file serving in production
    try:
        from whitenoise import WhiteNoise

        app.wsgi_app = WhiteNoise(app.wsgi_app, root=os.path.join(os.path.dirname(__file__), 'static'), prefix='static/')
    except Exception:
        # whitenoise is optional during local development if not installed
        pass

    # Create DB tables on startup (idempotent)
    try:
        with app.app_context():
            db.create_all()
    except Exception:
        # if the DB isn't reachable yet, let the app still start; failures will show in logs
        pass

    return app


# Provide a default app object for simple WSGI runners (gunicorn expects `app`)
try:
    app = create_app()
except Exception:
    app = None


if __name__ == '__main__':
    # When run directly, bind to the PORT env var (Railway compatibility)
    port = int(os.getenv('PORT', 5000))
    if app:
        app.run(host='0.0.0.0', port=port)
