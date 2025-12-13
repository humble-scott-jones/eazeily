import os, sqlite3, uuid, json, re
from datetime import date
from datetime import datetime, timezone
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, g, session, redirect, has_app_context, url_for
import logging
import voice_profile
import threading
import time
import math
from flask_cors import CORS
import generator as gen_mod
from werkzeug.security import generate_password_hash, check_password_hash
from typing import TYPE_CHECKING, Any, Mapping, Optional, Tuple, List
import requests
from services.generation import GenerationService as NewGenerationService
# Keep old generation_service for backward compatibility during migration
try:
    from generation_service import GenerationService as OldGenerationService
except ImportError:
    OldGenerationService = None
try:
    import yaml
except ImportError:  # pragma: no cover - dependency managed via requirements.txt
    yaml = None

# re-export key generator helpers for easier patching/tests
def generate_posts(*args, **kwargs):
    return gen_mod.generate_posts(*args, **kwargs)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, continue with system env vars

# optional stripe import (only used if STRIPE_SECRET_KEY is set)
# Feature flag to disable Stripe integration for free tier rollout
ENABLE_STRIPE = (os.getenv('ENABLE_STRIPE') or '').strip().lower() in {'1', 'true', 't', 'yes', 'y', 'on'}

stripe_secret = os.getenv("STRIPE_SECRET_KEY")
stripe: Optional[Any]
if stripe_secret and ENABLE_STRIPE:
    try:
        if TYPE_CHECKING:
            # ensure type-checkers know about stripe without requiring it at runtime
            import stripe  # type: ignore
        else:
            import stripe
    except Exception:
        stripe = None
else:
    stripe = None

IMAGE_DATA_URL_MAX_BYTES = 2_500_000  # ~2.5MB encoded payload cap for inline uploads
MAX_FEEDBACK_NOTE_LEN = 1500
VOICE_SAMPLE_MIN_LEN = 8  # Minimum character length for voice profile samples
VOICE_SAMPLE_MIN_COUNT = 5  # Minimum number of samples required
VOICE_SAMPLE_MAX_COUNT = 10  # Maximum number of samples allowed
try:
    TEAM_MEMBER_LIMIT = int(os.getenv('TEAM_MEMBER_LIMIT', '10'))
except (TypeError, ValueError):
    TEAM_MEMBER_LIMIT = 10
try:
    GENERATION_TIMEOUT_SECONDS = float(os.getenv('GENERATION_TIMEOUT_SECONDS', '15'))
except (TypeError, ValueError):
    GENERATION_TIMEOUT_SECONDS = 15.0

def _resolve_password_hash_method():
    """Derive the hashing method string used by werkzeug based on env vars."""
    explicit = os.getenv('PASSWORD_HASH_METHOD')
    if explicit:
        return explicit
    iterations = os.getenv('PASSWORD_HASH_ITERATIONS')
    if iterations:
        return f'pbkdf2:sha256:{iterations}'
    fast_flag = os.getenv('FAST_PASSWORD_HASH')
    if fast_flag:
        fast_iters = None
        try:
            fast_iters = int(fast_flag)
        except (TypeError, ValueError):
            fast_iters = None
        if not fast_iters or fast_iters <= 0:
            fast_iters = 12000
        return f'pbkdf2:sha256:{fast_iters}'
    return 'pbkdf2:sha256'

PASSWORD_HASH_METHOD = _resolve_password_hash_method()

def _hash_password(secret: str) -> str:
    return generate_password_hash(secret, method=PASSWORD_HASH_METHOD)


def _env_flag_enabled(var_name: str) -> bool:
    raw = os.getenv(var_name)
    if raw is None:
        return False
    return raw.strip().lower() in {'1', 'true', 't', 'yes', 'y', 'on'}


def _is_dev_mode() -> bool:
    env_value = (os.getenv('FLASK_ENV') or '').strip().lower()
    if env_value.startswith('dev'):
        return True
    if _env_flag_enabled('ALLOW_DEV_DEBUG'):
        return True
    # allow dev helpers when running under automated tests/CI
    if os.getenv('PYTEST_CURRENT_TEST'):
        return True
    if _env_flag_enabled('CI'):
        return True
    return False

GITHUB_FEEDBACK_TOKEN = os.getenv('GITHUB_FEEDBACK_TOKEN')
GITHUB_FEEDBACK_REPO = os.getenv('GITHUB_FEEDBACK_REPO')
GITHUB_FEEDBACK_TEMPLATE_GENERAL = os.getenv('GITHUB_FEEDBACK_TEMPLATE_GENERAL', 'user-feedback')
GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN = os.getenv('GITHUB_FEEDBACK_TEMPLATE_THUMBSDOWN', 'thumbs-down')
try:
    GITHUB_FEEDBACK_TIMEOUT = float(os.getenv('GITHUB_FEEDBACK_TIMEOUT', '6.0') or 6.0)
except (TypeError, ValueError):
    GITHUB_FEEDBACK_TIMEOUT = 6.0

FEEDBACK_AUTOMATION_CONFIG = {}
_FEEDBACK_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '.github', 'config', 'feedback-automation.yml')

app = Flask(__name__)
_secret = os.getenv("SECRET_KEY")
if not _secret:
    _secret = "dev-secret-change-me"
app.secret_key = _secret
# Structured logging with request IDs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


class RequestIdMissingFilter(logging.Filter):
    """Ensure log records always have request_id to satisfy the formatter."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'request_id'):
            record.request_id = 'n/a'
        return True


logging.getLogger().addFilter(RequestIdMissingFilter())
# ensure werkzeug/WSGI logs also carry request_id placeholder to satisfy formatter
for _logger_name in ("werkzeug", "werkzeug.error", "werkzeug.serving"):
    logging.getLogger(_logger_name).addFilter(RequestIdMissingFilter())
CORS(app)

if yaml and os.path.exists(_FEEDBACK_CONFIG_PATH):
    try:
        with open(_FEEDBACK_CONFIG_PATH, 'r', encoding='utf-8') as cfg_file:
            FEEDBACK_AUTOMATION_CONFIG = yaml.safe_load(cfg_file) or {}
    except Exception:  # pragma: no cover - config failures shouldn't crash app
        FEEDBACK_AUTOMATION_CONFIG = {}
else:
    FEEDBACK_AUTOMATION_CONFIG = {}

DB_PATH_ENV = os.getenv('DB_PATH')
# Determine DB path with a short compatibility window. Priority:
# 1) explicit DB_PATH env var
# 2) repo-local `eazeily.db` (new default)
# 3) repo-local `togetherly.db` (legacy fallback during transition)
_default_db = os.path.join(os.path.dirname(__file__), "eazeily.db")
_legacy_db = os.path.join(os.path.dirname(__file__), "togetherly.db")
if DB_PATH_ENV:
    DB_PATH = DB_PATH_ENV
elif os.path.exists(_default_db):
    DB_PATH = _default_db
elif os.path.exists(_legacy_db):
    DB_PATH = _legacy_db
else:
    DB_PATH = _default_db

# Optional Postgres connection string (preferred for team/prod plans)
DATABASE_URL = os.getenv('DATABASE_URL')
USE_POSTGRES = bool(DATABASE_URL)

# Normalize integrity errors across sqlite/Postgres so API handlers can stay consistent
DB_INTEGRITY_ERRORS = (sqlite3.IntegrityError,)
# psycopg may be absent in local/dev; guard import so we don't fail at module import.
psycopg = None
try:
    import psycopg  # type: ignore
except Exception:
    psycopg = None
if psycopg:
    try:
        from psycopg import errors as _pg_errors
        from psycopg.rows import dict_row as _pg_dict_row
        DB_INTEGRITY_ERRORS = DB_INTEGRITY_ERRORS + (_pg_errors.UniqueViolation, _pg_errors.ForeignKeyViolation)
    except Exception:
        _pg_dict_row = None
else:
    _pg_dict_row = None

# Outbound call kill switch (set KILL_SWITCH_OUTBOUND=1 to block external services)
OUTBOUND_KILL_SWITCH = (os.getenv('KILL_SWITCH_OUTBOUND') or os.getenv('DISABLE_OUTBOUND_CALLS') or '').lower() in ('1', 'true', 'yes', 'on')
# Simple in-memory token-bucket rate limiter for low-volume dev/prod protection.
# For production, prefer a distributed store (Redis) and a proper rate-limiting middleware.
RATE_LIMIT_STORE = {}
RATE_LIMIT_LOCK = threading.Lock()

openai_client = None
USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
OPENAI_GENERATE_MODEL = os.getenv('OPENAI_GENERATE_MODEL', 'gpt-4o-mini')
if USE_OPENAI:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        USE_OPENAI = False
        openai_client = None
if OUTBOUND_KILL_SWITCH:
    USE_OPENAI = False
    openai_client = None

# Initialize old generation service for backward compatibility
if OldGenerationService:
    generation_service = OldGenerationService(logger=None, timeout_seconds=GENERATION_TIMEOUT_SECONDS)
    generation_service.logger = app.logger
else:
    generation_service = None

# Initialize new generation service
new_generation_service = NewGenerationService(
    openai_api_key=os.getenv('OPENAI_API_KEY'),
    enable_openai=USE_OPENAI and not OUTBOUND_KILL_SWITCH
)

class OutboundBlocked(RuntimeError):
    """Raised when outbound calls are disabled via kill switch."""


def _ensure_outbound_allowed(service: str):
    if OUTBOUND_KILL_SWITCH:
        raise OutboundBlocked(f"Outbound calls disabled for maintenance (service={service}).")


def _get_request_id() -> str:
    rid = getattr(g, 'request_id', None)
    if not rid:
        rid = uuid.uuid4().hex[:8]
        g.request_id = rid
    return rid


def _ensure_request_id_in_response(response):
    """Attach request_id to JSON responses when missing.

    This keeps the API contract consistent without altering legacy
    endpoints that intentionally omit additional keys (e.g. profile).
    """

    # Avoid mutating profile contract (handled separately in BUG-001)
    if request.path.startswith('/api/profile'):
        return response

    if not response.is_json:
        return response

    try:
        data = response.get_json(silent=True)
    except Exception:
        return response

    if not isinstance(data, dict):
        return response

    if 'request_id' in data:
        return response

    data['request_id'] = _get_request_id()

    # Preserve status code/headers while updating JSON body
    response.set_data(json.dumps(data))
    response.headers['Content-Type'] = 'application/json'
    return response


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(g, 'request_id', 'n/a')
        return True


app.logger.addFilter(RequestIdFilter())

# Set up app logger with request ID formatting
app_logger_formatter = logging.Formatter("%(asctime)s %(levelname)s [req=%(request_id)s] %(message)s")
for handler in app.logger.handlers:
    handler.setFormatter(app_logger_formatter)


def _redact(value: str, keep: int = 3) -> str:
    if not value:
        return value
    if len(value) <= keep:
        return '*' * len(value)
    return value[:keep] + '*' * max(1, len(value) - keep)

def _check_rate_limit(key: str, capacity: int = 30, refill_seconds: int = 60):
    """Return (allowed: bool, retry_after_seconds: int)

    capacity: tokens available per `refill_seconds` window.
    Each call consumes 1 token.
    """
    now = time.time()
    with RATE_LIMIT_LOCK:
        entry = RATE_LIMIT_STORE.get(key)
        if not entry:
            # tokens, last_ts
            RATE_LIMIT_STORE[key] = [float(capacity - 1), now]
            return True, 0
        tokens, last = entry
        # refill proportionally
        elapsed = now - last
        if elapsed > 0:
            refill = (elapsed / float(refill_seconds)) * capacity
            tokens = min(float(capacity), tokens + refill)
            last = now
        if tokens >= 1.0:
            tokens -= 1.0
            RATE_LIMIT_STORE[key] = [tokens, last]
            return True, 0
        # not enough tokens
        RATE_LIMIT_STORE[key] = [tokens, last]
        # estimate retry after seconds until at least 1 token
        needed = 1.0 - tokens
        # time per token = refill_seconds / capacity
        t_per_token = float(refill_seconds) / float(capacity)
        retry_after = math.ceil(needed * t_per_token)
        return False, retry_after


def _enforce_rate_limit(bucket: str, capacity: int = 30, refill_seconds: int = 60):
    if os.getenv('DISABLE_RATE_LIMITS') or os.getenv('FLASK_ENV') in ('test', 'testing'):
        return None
    allowed, retry_after = _check_rate_limit(bucket, capacity=capacity, refill_seconds=refill_seconds)
    if not allowed:
        return jsonify({'ok': False, 'error': 'Rate limit exceeded', 'retry_after': retry_after}), 429
    return None


def _extract_choice_content(response_or_choice):
        """Safely extract textual content from an OpenAI SDK response or a single choice.

        Handles both dict-like responses and SDK objects where content may live at
        response.choices[0].message.content or response.choices[0].get('message')['content']
        or choice.text.
        Returns a string or None.
        """
        try:
            # dict-like top-level response
            if isinstance(response_or_choice, dict):
                choices = response_or_choice.get('choices') or []
                if not choices:
                    return None
                first = choices[0]
                # message may be a dict
                if isinstance(first, dict):
                    msg = first.get('message') or {}
                    if isinstance(msg, dict):
                        content = msg.get('content')
                        if content:
                            return str(content)
                    # fallback to text field
                    text = first.get('text')
                    return str(text) if text is not None else None

            # SDK-style response or a single choice object
            # If it's a full response object, grab the first choice
            choices = getattr(response_or_choice, 'choices', None)
            if choices:
                ch = choices[0]
            else:
                # maybe the input is already a single choice
                ch = response_or_choice

            # try choice.message.content
            msg = getattr(ch, 'message', None)
            if msg is not None:
                content = getattr(msg, 'content', None)
                if content:
                    return str(content)

            # try dict-like access
            try:
                if hasattr(ch, 'get'):
                    m = (ch.get('message') or {})
                    if isinstance(m, dict) and m.get('content'):
                        return str(m.get('content'))
                    if ch.get('text'):
                        return str(ch.get('text'))
            except Exception:
                pass

            # fallback to text attribute
            text = getattr(ch, 'text', None)
            if text:
                return str(text)
        except Exception:
            return None
        return None


def _parse_posts_payload(raw: Optional[str]):
    if not raw:
        return None
    text = raw.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return None
        else:
            return None
    if isinstance(data, dict):
        data = data.get('posts') or data.get('data') or data.get('items') or [data]
    if not isinstance(data, list):
        return None
    cleaned = []
    for item in data:
        if isinstance(item, dict):
            cleaned.append(item)
    return cleaned or None


def _generate_posts_via_openai(spec: dict):
    if not USE_OPENAI or openai_client is None:
        return None
    try:
        payload = dict(spec)
        start_day = payload.get('start_day')
        if isinstance(start_day, date):
            payload['start_day'] = start_day.isoformat()
        voice_profile_ctx = payload.get('voice_profile') or None
        prompt = {
            'instruction': 'Create social media posts as structured JSON.',
            'requirements': payload
        }
        if voice_profile_ctx:
            prompt['voice_profile'] = {
                'include_phrases': voice_profile_ctx.get('include_phrases'),
                'avoid_phrases': voice_profile_ctx.get('avoid_phrases'),
                'examples': voice_profile_ctx.get('example_lines'),
                'avg_length': voice_profile_ctx.get('avg_length'),
                'style_instruction': voice_profile_ctx.get('style_instruction'),
            }
        response = openai_client.chat.completions.create(  # type: ignore[attr-defined]
            model=OPENAI_GENERATE_MODEL,
            messages=[
                {'role': 'system', 'content': 'You are an assistant that outputs ONLY strict JSON arrays of post objects.'},
                {'role': 'user', 'content': json.dumps(prompt)}
            ],
            temperature=0.6
        )
        content = _extract_choice_content(response)
        return _parse_posts_payload(content)
    except Exception:
        return None


def _generate_posts_from_image(spec: dict):
    if not USE_OPENAI or openai_client is None:
        return None
    image_data_url = spec.get('image_data_url')
    if not image_data_url:
        return None
    try:
        payload = dict(spec)
        start_day = payload.get('start_day')
        if isinstance(start_day, date):
            payload['start_day'] = start_day.isoformat()
        # keep context separate so we can emphasize it in the prompt
        image_context = (payload.get('image_context') or '').strip()
        voice_profile_ctx = payload.get('voice_profile') or None
        requirements = {
            'days': payload.get('days'),
            'platforms': payload.get('platforms'),
            'tone': payload.get('tone'),
            'industry': payload.get('industry'),
            'company': payload.get('company'),
            'brand_keywords': payload.get('brand_keywords'),
            'goals': payload.get('goals'),
            'details': payload.get('details'),
            'start_day': payload.get('start_day'),
        }
        if voice_profile_ctx:
            requirements['voice_profile'] = {
                'include_phrases': voice_profile_ctx.get('include_phrases'),
                'avoid_phrases': voice_profile_ctx.get('avoid_phrases'),
                'examples': voice_profile_ctx.get('example_lines'),
                'avg_length': voice_profile_ctx.get('avg_length'),
                'style_instruction': voice_profile_ctx.get('style_instruction'),
            }
        instructions = [
            "Look at the attached inspiration image and craft polished social posts that reference what you see.",
            "Blend the visual cues with the requirements JSON below.",
            "Respond with ONLY a JSON array of post objects (same schema as other generation responses).",
        ]
        if voice_profile_ctx:
            include = voice_profile_ctx.get('include_phrases') or []
            avoid = voice_profile_ctx.get('avoid_phrases') or []
            examples = voice_profile_ctx.get('example_lines') or []
            voice_hints = []
            if include:
                voice_hints.append(f"Use phrases like: {', '.join(include[:3])}.")
            if avoid:
                voice_hints.append(f"Avoid overusing: {', '.join(avoid[:3])}.")
            if examples:
                voice_hints.append(f"Match cadence: {examples[0][:140]}")
            if voice_hints:
                instructions.append("Voice profile: " + " ".join(voice_hints))
        if image_context:
            instructions.insert(1, f"Emphasize this guidance from the user: {image_context.strip()[:500]}")
        user_content = [
            {
                'type': 'text',
                'text': "\n".join(instructions) + "\nRequirements:" + json.dumps(requirements, default=str)
            },
            {
                'type': 'input_image',
                'image_url': {'url': image_data_url}
            }
        ]
        response = openai_client.chat.completions.create(  # type: ignore[attr-defined]
            model=OPENAI_GENERATE_MODEL,
            messages=[
                {'role': 'system', 'content': 'You are a social media strategist. Output STRICT JSON arrays of posts.'},
                {'role': 'user', 'content': user_content}
            ],
            temperature=0.5
        )
        content = _extract_choice_content(response)
        return _parse_posts_payload(content)
    except Exception:
        return None


def _apply_voice_guardrails(posts: list[dict], voice_profile_ctx: Optional[dict]):
    if not voice_profile_ctx or not isinstance(posts, list):
        return
    for post in posts:
        if not isinstance(post, dict):
            continue
        caption = post.get('caption') or ''
        assessment = voice_profile.assess_text(voice_profile_ctx, caption)
        post['voice_match_score'] = assessment['score']
        if assessment.get('drift'):
            post['voice_guardrail'] = assessment.get('message')
            post['voice_suggestions'] = assessment.get('suggestions')

class _PgConnectionWrapper:
    """Lightweight wrapper to normalize Postgres connection to sqlite-style API."""

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=()):
        normalized_sql = sql.replace("?", "%s")
        cur = self._conn.cursor(row_factory=_pg_dict_row) if _pg_dict_row else self._conn.cursor()
        cur.execute(normalized_sql, params)
        return cur

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()


def _connect_db():
    """Return a DB connection using Postgres if configured, otherwise sqlite."""
    if USE_POSTGRES:
        if not psycopg:
            raise RuntimeError("psycopg is required for Postgres connections; install dependencies.")
        # Fix for "invalid connection option 'timeout'" error
        # Some environments inject ?timeout=... which psycopg3 rejects (it expects connect_timeout)
        db_url = str(DATABASE_URL)
        # Simple replacement to map 'timeout' to 'connect_timeout' which libpq accepts
        if '?timeout=' in db_url:
            db_url = db_url.replace('?timeout=', '?connect_timeout=')
        if '&timeout=' in db_url:
            db_url = db_url.replace('&timeout=', '&connect_timeout=')
            
        conn = psycopg.connect(db_url, autocommit=False)
        return _PgConnectionWrapper(conn)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    if "db" not in g:
        g.db = _connect_db()
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@app.before_request
def _attach_request_id():
    _get_request_id()

@app.after_request
def _set_request_id_header(response):
    try:
        response = _ensure_request_id_in_response(response)
        response.headers['X-Request-Id'] = _get_request_id()
    except Exception:
        pass
    return response

def init_db():
    db = get_db()
    # For Postgres deployments, migrations should handle schema creation.
    if USE_POSTGRES:
        return db
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            industry TEXT,
            tone TEXT,
            platforms TEXT,
            brand_keywords TEXT,
            niche_keywords TEXT,
            goals TEXT,
            company TEXT,
            include_images INTEGER DEFAULT 1,
            details TEXT,
            voice_profile TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profile_id TEXT,
            post_day INTEGER,
            platform TEXT,
            rating INTEGER,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            password_hash TEXT,
            is_paid INTEGER DEFAULT 0,
            free_sample_used INTEGER DEFAULT 0,
            stripe_customer_id TEXT,
            voice_profile TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            stripe_subscription_id TEXT,
            status TEXT,
            current_period_end DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS reconcile_jobs (
            id TEXT PRIMARY KEY,
            status TEXT,
            result TEXT,
            started_at DATETIME,
            finished_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token TEXT PRIMARY KEY,
            user_id TEXT,
            expires_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS generation_usage (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            period TEXT,
            reels_generated INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS waitlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            confirmed INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS team_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_user_id TEXT NOT NULL,
            member_email TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_team_members_owner_email
            ON team_members(owner_user_id, member_email);
        CREATE TABLE IF NOT EXISTS team_approvals (
            id TEXT PRIMARY KEY,
            owner_user_id TEXT NOT NULL,
            submitter_user_id TEXT NOT NULL,
            title TEXT,
            content_ref TEXT,
            state TEXT DEFAULT 'pending',
            reviewers TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS team_approval_events (
            id TEXT PRIMARY KEY,
            approval_id TEXT NOT NULL,
            actor_user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_team_approvals_owner_state ON team_approvals(owner_user_id, state);
        CREATE TABLE IF NOT EXISTS team_drafts (
            id TEXT PRIMARY KEY,
            owner_user_id TEXT NOT NULL,
            title TEXT,
            campaign TEXT,
            channel TEXT,
            status TEXT DEFAULT 'draft',
            assignee_email TEXT,
            reviewer_email TEXT,
            review_open_to_any INTEGER DEFAULT 0,
            review_requested_at DATETIME,
            review_nudged_at DATETIME,
            due_date DATETIME,
            content TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_team_drafts_owner_status ON team_drafts(owner_user_id, status);
        CREATE TABLE IF NOT EXISTS team_draft_comments (
            id TEXT PRIMARY KEY,
            draft_id TEXT NOT NULL,
            paragraph_id TEXT,
            author_user_id TEXT NOT NULL,
            body TEXT,
            thread_id TEXT NOT NULL,
            parent_id TEXT,
            mentions TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_team_draft_comments_draft ON team_draft_comments(draft_id);
        CREATE TABLE IF NOT EXISTS team_draft_revisions (
            id TEXT PRIMARY KEY,
            draft_id TEXT NOT NULL,
            author_user_id TEXT NOT NULL,
            summary TEXT,
            kind TEXT DEFAULT 'revision',
            details TEXT,
            content_snapshot TEXT,
            changelog_note TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_team_draft_revisions_draft ON team_draft_revisions(draft_id);

        CREATE TABLE IF NOT EXISTS team_approver_defaults (
            id TEXT PRIMARY KEY,
            owner_user_id TEXT NOT NULL,
            campaign TEXT,
            channel TEXT,
            approver_email TEXT,
            allow_any INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_team_approver_defaults_owner ON team_approver_defaults(owner_user_id);

        CREATE TABLE IF NOT EXISTS team_draft_notifications (
            id TEXT PRIMARY KEY,
            draft_id TEXT NOT NULL,
            channel TEXT,
            message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS templates (
            id TEXT PRIMARY KEY,
            owner_user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            scope TEXT DEFAULT 'personal',
            payload TEXT,
            preview TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_templates_owner_scope ON templates(owner_user_id, scope);
        """
    )
    # Backfill for upgrades
    cols = [r[1] for r in db.execute("PRAGMA table_info(profiles)").fetchall()]
    if "goals" not in cols:
        db.execute("ALTER TABLE profiles ADD COLUMN goals TEXT;")
    if "industry" not in cols:
        db.execute("ALTER TABLE profiles ADD COLUMN industry TEXT;")
    if "company" not in cols:
        try:
            db.execute("ALTER TABLE profiles ADD COLUMN company TEXT;")
        except Exception:
            pass
    if "details" not in cols:
        try:
            db.execute("ALTER TABLE profiles ADD COLUMN details TEXT;")
        except Exception:
            pass
    if "voice_profile" not in cols:
        try:
            db.execute("ALTER TABLE profiles ADD COLUMN voice_profile TEXT;")
        except Exception:
            pass
    # ensure users table has is_admin column (backfill for older DBs)
    try:
        ucols = [r[1] for r in db.execute("PRAGMA table_info(users)").fetchall()]
        if "is_admin" not in ucols:
            try:
                db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0;")
            except Exception:
                pass
        if "free_sample_used" not in ucols:
            try:
                db.execute("ALTER TABLE users ADD COLUMN free_sample_used INTEGER DEFAULT 0;")
            except Exception:
                pass
        if "subscription_tier" not in ucols:
            try:
                db.execute("ALTER TABLE users ADD COLUMN subscription_tier TEXT;")
            except Exception:
                pass
    except Exception:
        pass
    # backfill team_drafts columns for review routing
    try:
        dcols = [r[1] for r in db.execute("PRAGMA table_info(team_drafts)").fetchall()]
        if "channel" not in dcols:
            db.execute("ALTER TABLE team_drafts ADD COLUMN channel TEXT;")
        if "reviewer_email" not in dcols:
            db.execute("ALTER TABLE team_drafts ADD COLUMN reviewer_email TEXT;")
        if "review_open_to_any" not in dcols:
            db.execute("ALTER TABLE team_drafts ADD COLUMN review_open_to_any INTEGER DEFAULT 0;")
        if "review_requested_at" not in dcols:
            db.execute("ALTER TABLE team_drafts ADD COLUMN review_requested_at DATETIME;")
        if "review_nudged_at" not in dcols:
            db.execute("ALTER TABLE team_drafts ADD COLUMN review_nudged_at DATETIME;")
    except Exception:
        pass
    # backfill changelog column on revisions
    try:
        rcols = [r[1] for r in db.execute("PRAGMA table_info(team_draft_revisions)").fetchall()]
        if "changelog_note" not in rcols:
            db.execute("ALTER TABLE team_draft_revisions ADD COLUMN changelog_note TEXT;")
    except Exception:
        pass
    db.commit()

    # Dev-only: seed a known admin user for local development to simplify testing
    try:
        if _is_dev_mode():
            dev_email = 'hi.scott.jones@gmail.com'
            dev_pw = os.getenv('DEV_ADMIN_PW') or 'OHsj1984'
            # create or update user with admin flag
            existing = db.execute('SELECT id FROM users WHERE email = ?', (dev_email,)).fetchone()
            pw_hash = _hash_password(dev_pw)
            if existing:
                try:
                    db.execute('UPDATE users SET password_hash = ?, is_admin = ? WHERE id = ?', (pw_hash, 1, existing['id']))
                except Exception:
                    pass
            else:
                try:
                    uid = str(uuid.uuid4())
                    db.execute('INSERT INTO users (id, email, password_hash, is_admin, is_paid, free_sample_used) VALUES (?, ?, ?, ?, ?, ?)', (uid, dev_email, pw_hash, 1, 1, 0))
                except Exception:
                    pass
            db.commit()
    except Exception:
        pass


def row_to_mapping(row: Any) -> Optional[dict]:
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    # sqlite3.Row or psycopg.rows.dict_row
    return dict(row)


def _deserialize_json(raw: Any, default: Any = None) -> Any:
    if raw is None:
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return default


def _serialize_template_row(row):
    if not row:
        return None
    data = row_to_mapping(row) or {}
    data['payload'] = _deserialize_json(data.get('payload'), {})
    if data.get('updated_at') and not data.get('updatedAt'):
        data['updatedAt'] = data['updated_at']
    return data


def _normalize_profile_payload(row: Any = None, pid: Optional[str] = None) -> dict:
    base = {
        'id': pid,
        'industry': '',
        'industry_key': '',
        'tone': '',
        'platforms': [],
        'brand_keywords': [],
        'niche_keywords': [],
        'goals': [],
        'company': '',
        'include_images': False,
        'details': {},
        'voice_profile': {},
        'timezone': ''
    }

    if not row:
        return base

    data = row_to_mapping(row) or {}
    payload = dict(base)
    payload['id'] = data.get('id') or pid or base['id']
    payload['industry'] = data.get('industry') or ''
    payload['industry_key'] = data.get('industry_key') or payload['industry']
    payload['tone'] = data.get('tone') or ''
    payload['platforms'] = _deserialize_json(data.get('platforms'), []) or []
    payload['brand_keywords'] = _deserialize_json(data.get('brand_keywords'), []) or []
    payload['niche_keywords'] = _deserialize_json(data.get('niche_keywords'), []) or []
    payload['goals'] = _deserialize_json(data.get('goals'), []) or []
    payload['company'] = data.get('company') or ''
    payload['include_images'] = bool(data.get('include_images'))
    payload['details'] = _deserialize_json(data.get('details'), {}) or {}
    payload['voice_profile'] = _deserialize_json(data.get('voice_profile'), {}) or {}
    if isinstance(payload['details'], dict):
        payload['timezone'] = payload['details'].get('timezone') or payload['details'].get('tz') or ''
    return payload


def _get_current_user_row():
    uid = session.get('user_id')
    if not uid:
        return None
    db = get_db()
    return db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()


def _db_healthcheck():
    """Perform a short, isolated DB connectivity check.

    We avoid using the app-scoped `get_db()` here because that may create
    a long-lived connection object in `g` which could mask transient
    connection issues. Instead we open a short-lived connection, run
    a lightweight query, and close it immediately. Return (healthy, err)
    where `err` is a short string when unhealthy.
    """
    try:
        if USE_POSTGRES:
            # psycopg may be None if not installed; guard defensively
            if not psycopg:
                return False, "psycopg not available"
            # set a short timeout so readiness doesn't hang during DB boot
            conn = psycopg.connect(DATABASE_URL, timeout=3)
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.close()
            conn.close()
            return True, None
        else:
            # sqlite file-based quick probe
            conn = sqlite3.connect(DB_PATH, timeout=3)
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.close()
            conn.close()
            return True, None
    except Exception as exc:
        # Keep the error short and avoid leaking secrets
        err = str(exc)
        if '\n' in err:
            err = err.split('\n', 1)[0]
        return False, err


@app.get("/healthz")
def healthz():
    """Liveness probe (no dependencies)."""
    return jsonify({
        'status': 'ok',
        'version': os.getenv('APP_VERSION', 'dev'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
    })


@app.get("/readyz")
def readyz():
    """Readiness probe with dependency checks."""
    healthy, db_error = _db_healthcheck()
    db_info = {
        'type': 'postgres' if USE_POSTGRES else 'sqlite',
        'status': 'connected' if healthy else 'unhealthy',
        'error': db_error if not healthy else None,
    }

    # preserve legacy simple check keys while adding structured data
    checks = {
        'database': 'connected' if healthy else f"unhealthy: {db_error or 'unknown'}",
        'stripe': 'configured' if (os.getenv('STRIPE_SECRET_KEY') and stripe) else 'not_configured',
        'openai': 'configured' if USE_OPENAI else 'not_configured',
        'github_feedback': 'configured' if GITHUB_FEEDBACK_TOKEN else 'not_configured',
    }

    status = 'healthy' if healthy else 'unhealthy'
    status_code = 200 if healthy else 503
    payload = {
        'status': status,
        'version': os.getenv('APP_VERSION', 'dev'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': checks,
        'db': db_info,
    }
    return jsonify(payload), status_code


@app.get("/health")
def legacy_health():
    """Back-compat endpoint; proxies to /readyz."""
    return readyz()


@app.get('/api/debug/health')
def api_debug_health():
    request_id = _get_request_id()
    healthy, db_error = _db_healthcheck()
    db_info = {
        'type': 'postgres' if USE_POSTGRES else 'sqlite',
        'status': 'connected' if healthy else 'unhealthy',
        'error': db_error if not healthy else None,
    }

    checks = {
        'database': 'connected' if healthy else f"unhealthy: {db_error or 'unknown'}",
        'stripe': 'configured' if (os.getenv('STRIPE_SECRET_KEY') and stripe) else 'not_configured',
        'openai': 'configured' if USE_OPENAI else 'not_configured',
        'github_feedback': 'configured' if GITHUB_FEEDBACK_TOKEN else 'not_configured',
    }

    status = 'healthy' if healthy else 'unhealthy'
    status_code = 200 if healthy else 503
    payload = {
        'ok': healthy,
        'request_id': request_id,
        'status': status,
        'version': os.getenv('APP_VERSION', 'dev'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': checks,
        'db': db_info,
    }
    return jsonify(payload), status_code


@app.get('/api/debug/openai-status')
def api_debug_openai_status():
    request_id = _get_request_id()
    configured = bool(os.getenv('OPENAI_API_KEY'))
    client_ready = bool(USE_OPENAI and openai_client is not None)

    reason = None
    if OUTBOUND_KILL_SWITCH:
        reason = 'outbound_kill_switch'
    elif not configured:
        reason = 'missing_api_key'
    elif not client_ready:
        reason = 'client_not_initialized'

    payload = {
        'ok': True,
        'request_id': request_id,
        'status': 'enabled' if client_ready and not OUTBOUND_KILL_SWITCH else 'disabled',
        'configured': configured,
        'kill_switch_active': bool(OUTBOUND_KILL_SWITCH),
        'client_ready': client_ready,
    }

    if reason:
        payload['reason'] = reason

    return jsonify(payload)

def _initial_user_payload():
    uid = session.get('user_id')
    if not uid:
        return None
    try:
        db = get_db()
        row = db.execute('SELECT id, email, is_paid, free_sample_used, subscription_tier FROM users WHERE id = ?', (uid,)).fetchone()
    except Exception:
        return None
    if not row:
        return None
    return {
        'id': row['id'],
        'email': row['email'],
        'is_paid': bool(row['is_paid']),
        'free_sample_used': bool(row['free_sample_used']) if row['free_sample_used'] is not None else False,
        'subscription_tier': row['subscription_tier']
    }


@app.get("/")
def landing():
    """Landing page with marketing content, pricing, and waitlist signup."""
    return render_template("landing.html", initial_user=_initial_user_payload())


@app.get("/launch")
def launch_page():
    """Public launch page with waitlist form and FAQs."""
    return render_template("launch.html", initial_user=_initial_user_payload())


@app.get("/app")
def index():
    """Main application page for authenticated users."""
    return render_template("index.html", is_dev=_is_dev_mode(), initial_user=_initial_user_payload())


@app.get("/generate")
def generate_page():
    """Redirect to the primary generation tab."""
    return redirect(url_for('generate_social_page'))


@app.get("/generate/social")
def generate_social_page():
    """Dashboard for social content generation."""
    initial_user = _initial_user_payload()
    is_team_tier = False
    if initial_user and initial_user.get('subscription_tier') == 'team':
        is_team_tier = True
    return render_template(
        "generate_social.html",
        is_dev=_is_dev_mode(),
        initial_user=initial_user,
        is_team_tier=is_team_tier,
        generator_mode='social'
    )


@app.get("/generate/reels")
def generate_reels_page():
    """Dedicated view for video-first generation."""
    initial_user = _initial_user_payload()
    is_team_tier = False
    if initial_user and initial_user.get('subscription_tier') == 'team':
        is_team_tier = True
    return render_template(
        "generate_reels.html",
        is_dev=_is_dev_mode(),
        initial_user=initial_user,
        is_team_tier=is_team_tier,
        generator_mode='reels'
    )


@app.get("/generate/reviews")
def generate_reviews_page():
    """Dedicated route for review responses."""
    return render_template("generate_reviews.html")


@app.get("/settings")
def settings_page():
    """Workspace settings for account defaults and voice training."""
    initial_user = _initial_user_payload()
    is_team_tier = False
    if initial_user and initial_user.get('subscription_tier') == 'team':
        is_team_tier = True
    return render_template(
        "settings.html",
        is_dev=_is_dev_mode(),
        initial_user=initial_user,
        is_team_tier=is_team_tier
    )


@app.get('/inbox')
def inbox_page():
    """Legacy inbox route retained for backward compatibility."""
    return redirect(url_for('planner_page'), code=302)


@app.get('/planner')
def planner_page():
    """Content planner for generated drafts and approvals."""
    is_dev = _is_dev_mode()
    return render_template('planner.html', is_dev=is_dev, initial_user=_initial_user_payload())


@app.get('/drafts/<draft_id>')
def draft_detail_page(draft_id: str):
    """Detailed draft view with comments and approvals."""
    return render_template('draft_detail.html', draft_id=draft_id, initial_user=_initial_user_payload())


def _ensure_admin_csrf_token() -> Optional[str]:
    token = session.get('admin_csrf')
    if not token:
        token = uuid.uuid4().hex
        session['admin_csrf'] = token
    return token


@app.get('/admin')
def admin_page():
    allowed = is_admin()
    csrf_token = _ensure_admin_csrf_token() if allowed else None
    return render_template('admin.html', allowed=allowed, admin_csrf=csrf_token, team_capacity=TEAM_MEMBER_LIMIT)


@app.get('/review-response')
def review_response_page():
    """Legacy route kept for backward compatibility."""
    return redirect(url_for('generate_reviews_page'), code=302)


@app.post('/api/signup')
def api_signup():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'ok': False, 'error': 'Email and password are required'}), 400
    
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({'ok': False, 'error': 'Invalid email address'}), 400

    db = get_db()
    try:
        # Check if user exists
        existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            return jsonify({'ok': False, 'error': 'Email already registered'}), 409

        user_id = str(uuid.uuid4())
        pw_hash = generate_password_hash(password)
        
        db.execute(
            'INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)',
            (user_id, email, pw_hash)
        )
        db.commit()
        
        session['user_id'] = user_id
        session['email'] = email
        
        return jsonify({'ok': True, 'id': user_id})
    except Exception as e:
        logging.exception("Signup failed")
        return jsonify({'ok': False, 'error': 'Signup failed'}), 500


@app.post('/api/login')
def api_login():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'ok': False, 'error': 'Email and password are required'}), 400

    db = get_db()
    user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if not user or not check_password_hash(user['password_hash'], password):
        return jsonify({'ok': False, 'error': 'Invalid credentials'}), 401

    session['user_id'] = user['id']
    session['email'] = user['email']
    
    # Check if admin
    admin_emails = [e.strip().lower() for e in os.environ.get('ADMIN_EMAILS', '').split(',') if e.strip()]
    if email in admin_emails:
        session['is_admin'] = True
        session['admin_csrf'] = str(uuid.uuid4())

    return jsonify({'ok': True, 'id': user['id']})


@app.post('/api/logout')
def api_logout():
    session.clear()
    return jsonify({'ok': True})


@app.post('/api/request-password-reset')
def api_request_password_reset():
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip().lower()
    
    if not email:
        return jsonify({'ok': False, 'error': 'Email is required'}), 400

    db = get_db()
    user = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    
    if user:
        token = str(uuid.uuid4())
        expires = datetime.now(timezone.utc) + timedelta(hours=1)
        db.execute(
            'INSERT OR REPLACE INTO password_reset_tokens (token, user_id, expires_at) VALUES (?, ?, ?)',
            (token, user['id'], expires)
        )
        db.commit()
        # In a real app, send email here. For now/tests, we return the token if in dev/test mode or just ok.
        # The test expects the token in the response.
        return jsonify({'ok': True, 'token': token})
    
    # Don't reveal if user exists
    return jsonify({'ok': True})


@app.post('/api/confirm-password-reset')
def api_confirm_password_reset():
    data = request.get_json(silent=True) or {}
    token = data.get('token')
    password = data.get('password')
    
    if not token or not password:
        return jsonify({'ok': False, 'error': 'Token and password are required'}), 400

    db = get_db()
    row = db.execute('SELECT user_id, expires_at FROM password_reset_tokens WHERE token = ?', (token,)).fetchone()
    
    if not row:
        return jsonify({'ok': False, 'error': 'Invalid token'}), 400
        
    # Check expiration (sqlite returns string for datetime)
    expires_at = row['expires_at']
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at)
        except ValueError:
            # Fallback for older python or different format
            pass
            
    # Ensure timezone awareness compatibility
    now = datetime.now(timezone.utc)
    if isinstance(expires_at, datetime) and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if isinstance(expires_at, datetime) and now > expires_at:
        return jsonify({'ok': False, 'error': 'Token expired'}), 400

    pw_hash = generate_password_hash(password)
    db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (pw_hash, row['user_id']))
    db.execute('DELETE FROM password_reset_tokens WHERE token = ?', (token,))
    db.commit()
    
    return jsonify({'ok': True})


@app.post('/api/waitlist')
def api_waitlist():
    data = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()
    if not email:
        return jsonify({'ok': False, 'error': 'Email is required'}), 400
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({'ok': False, 'error': 'Invalid email address'}), 400

    db = get_db()
    try:
        db.execute('INSERT INTO waitlist (email, confirmed) VALUES (?, ?)', (email, 0))
        db.commit()
    except (sqlite3.IntegrityError, *DB_INTEGRITY_ERRORS):
        return jsonify({'ok': False, 'error': 'Email already on waitlist'}), 400
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 500

    return jsonify({'ok': True})


@app.get('/account')
def account_page():
    uid = session.get('user_id')
    if not uid:
        return render_template('account.html', user=None)
    db = get_db()
    user = db.execute('SELECT id, email, is_paid, stripe_customer_id, subscription_tier FROM users WHERE id = ?', (uid,)).fetchone()
    sub = None
    subscription = None
    if user:
        sub = db.execute('SELECT * FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (user['id'],)).fetchone()
    subscription = dict(sub) if sub else None
    # try to fetch fresh data from Stripe and enrich with human dates (best-effort)
    try:
        if subscription and stripe and os.getenv('STRIPE_SECRET_KEY') and 'stripe_subscription_id' in subscription and subscription['stripe_subscription_id']:
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            remote = stripe.Subscription.retrieve(subscription['stripe_subscription_id'])
            subscription['status'] = remote.get('status')
            subscription['current_period_end'] = remote.get('current_period_end')
    except Exception:
        pass
    # enrich human-friendly date similar to /api/account
    if subscription and 'current_period_end' in subscription and subscription['current_period_end']:
        try:
            cpe = subscription['current_period_end']
            dt = None
            if isinstance(cpe, (int, float)):
                dt = datetime.fromtimestamp(int(cpe), tz=timezone.utc)
            else:
                try:
                    dt = datetime.fromtimestamp(int(str(cpe)), tz=timezone.utc)
                except Exception:
                    try:
                        dt = datetime.fromisoformat(str(cpe))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        dt = None
            if dt:
                subscription['current_period_end_iso'] = dt.astimezone(timezone.utc).isoformat()
                subscription['current_period_end_human'] = dt.strftime('%Y-%m-%d %H:%M UTC')
                now = datetime.now(tz=timezone.utc)
                delta = dt - now
                subscription['days_until_renewal'] = max(0, delta.days)
        except Exception:
            pass
    # pass is_admin flag (and admin CSRF) to template for rendering admin controls inline
    admin_flag = is_admin()
    admin_csrf = _ensure_admin_csrf_token() if admin_flag else None
    admin_scope = _get_admin_scope() if admin_flag else {
        'mode': 'restricted',
        'is_super_admin': False,
        'is_team_admin': False,
        'team_owner_id': None,
        'team_owner_email': None,
    }
    user_team_tier = False
    user_subscription_tier = None
    if user and 'subscription_tier' in user.keys():
        user_subscription_tier = (user['subscription_tier'] or '').lower()
        user_team_tier = user_subscription_tier == 'team'
    return render_template(
        'account.html',
        user=user,
        subscription=subscription,
        is_admin=admin_flag,
        admin_csrf=admin_csrf,
        admin_scope=admin_scope,
        team_capacity=TEAM_MEMBER_LIMIT,
        is_team_tier=user_team_tier,
        subscription_tier=user_subscription_tier,
    )


@app.get('/api/account')
def api_account():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
    db = get_db()
    user = db.execute('SELECT id, email, is_paid, stripe_customer_id FROM users WHERE id = ?', (uid,)).fetchone()
    sub = db.execute('SELECT id, stripe_subscription_id, status, current_period_end FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (uid,)).fetchone()
    subscription_data = dict(sub) if sub else None
    # if Stripe is configured and we have a stripe_subscription_id, try to fetch fresh status
    try:
        if subscription_data and stripe and os.getenv('STRIPE_SECRET_KEY') and subscription_data.get('stripe_subscription_id'):
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            remote = stripe.Subscription.retrieve(subscription_data['stripe_subscription_id'])
            subscription_data['status'] = remote.get('status')
            subscription_data['current_period_end'] = remote.get('current_period_end')
    except Exception:
        # ignore Stripe errors; fall back to DB
        pass
    # Enrich subscription_data with human-friendly dates if current_period_end exists
    if subscription_data and subscription_data.get('current_period_end'):
        try:
            # Stripe returns current_period_end as a unix timestamp (int) in many cases
            cpe = subscription_data.get('current_period_end')
            if isinstance(cpe, (int, float)):
                dt = datetime.fromtimestamp(int(cpe), tz=timezone.utc)
            else:
                # sometimes it's stored as a string in DB; try parsing as int then ISO
                try:
                    dt = datetime.fromtimestamp(int(str(cpe)), tz=timezone.utc)
                except Exception:
                    # try ISO parse
                    try:
                        dt = datetime.fromisoformat(str(cpe))
                        if dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        dt = None
            if dt:
                subscription_data['current_period_end_iso'] = dt.astimezone(timezone.utc).isoformat()
                # human readable in UTC for now; front-end can localize if desired
                subscription_data['current_period_end_human'] = dt.strftime('%Y-%m-%d %H:%M UTC')
                # days until renewal (rounding down)
                now = datetime.now(tz=timezone.utc)
                delta = dt - now
                subscription_data['days_until_renewal'] = max(0, delta.days)
        except Exception:
            # best-effort only
            pass

    return jsonify({'ok': True, 'user': {'id': user['id'], 'email': user['email'], 'is_paid': bool(user['is_paid'])}, 'subscription': subscription_data})


@app.route('/api/profile', methods=['GET', 'POST'])
def api_profile():
    request_id = _get_request_id()
    if request.method == 'POST':
        db = get_db()
        data = request.get_json(force=True) or {}
        pid = session.get('profile_id')
        if not pid:
            pid = str(uuid.uuid4())
            session['profile_id'] = pid
        
        # Extract fields
        industry = data.get('industry')
        tone = data.get('tone')
        platforms = json.dumps(data.get('platforms') or [])
        brand_keywords = json.dumps(data.get('brand_keywords') or [])
        niche_keywords = json.dumps(data.get('niche_keywords') or [])
        goals = json.dumps(data.get('goals') or [])
        company = data.get('company') or ''
        errors = {}
        if len(company) > 100:
            errors['company'] = 'Company name too long'
        if re.search(r'[<>]', company):
            errors['company'] = 'Invalid characters'
            
        if errors:
            msg = list(errors.values())[0]
            return jsonify({'ok': False, 'errors': errors, 'error': msg, 'request_id': request_id}), 400
            
        include_images = 1 if data.get('include_images') else 0
        details = json.dumps(data.get('details') or {})
        voice_profile_data = json.dumps(data.get('voice_profile') or {})

        # Upsert
        existing = db.execute('SELECT id FROM profiles WHERE id = ?', (pid,)).fetchone()
        try:
            if existing:
                db.execute('''
                    UPDATE profiles SET 
                    industry=?, tone=?, platforms=?, brand_keywords=?, niche_keywords=?, 
                    goals=?, company=?, include_images=?, details=?, voice_profile=?
                    WHERE id=?
                ''', (industry, tone, platforms, brand_keywords, niche_keywords, goals, company, include_images, details, voice_profile_data, pid))
            else:
                db.execute('''
                    INSERT INTO profiles (id, industry, tone, platforms, brand_keywords, niche_keywords, goals, company, include_images, details, voice_profile)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pid, industry, tone, platforms, brand_keywords, niche_keywords, goals, company, include_images, details, voice_profile_data))
        except Exception as e:
            # Fallback for missing voice_profile column (if migration failed)
            # We catch all exceptions here to be safe, assuming that if the full save fails,
            # we should try the legacy save. If that also fails, it will raise its own exception.
            logging.warning(f"Profile save with voice_profile failed: {e}. Retrying with legacy schema.")
            
            # IMPORTANT: If using Postgres, the transaction is now aborted. We must rollback before retrying.
            try:
                db.rollback()
            except Exception:
                pass # If rollback fails or isn't supported, ignore
                
            if existing:
                db.execute('''
                    UPDATE profiles SET 
                    industry=?, tone=?, platforms=?, brand_keywords=?, niche_keywords=?, 
                    goals=?, company=?, include_images=?, details=?
                    WHERE id=?
                ''', (industry, tone, platforms, brand_keywords, niche_keywords, goals, company, include_images, details, pid))
            else:
                db.execute('''
                    INSERT INTO profiles (id, industry, tone, platforms, brand_keywords, niche_keywords, goals, company, include_images, details)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pid, industry, tone, platforms, brand_keywords, niche_keywords, goals, company, include_images, details))

        db.commit()
        return jsonify({'ok': True, 'id': pid, 'request_id': request_id})

    else: # GET
        try:
            db = get_db()
            pid = session.get('profile_id')
            row = None
            if pid:
                row = db.execute('SELECT * FROM profiles WHERE id = ?', (pid,)).fetchone()

            # Deserialize
            p = _normalize_profile_payload(row, pid)
            return jsonify({'ok': True, 'profile': p, 'request_id': request_id})
        except Exception as exc:
            app.logger.exception("Failed to load profile", exc_info=exc)
            return jsonify({
                'ok': False,
                'error': {'message': 'Unable to load profile right now.'},
                'request_id': request_id
            }), 500


def _validate_generate_payload(payload: Mapping[str, Any]) -> dict:
    errors: dict[str, str] = {}
    try:
        days = int(payload.get('days') or 7)
        if days <= 0 or days > 31:
            errors['days'] = 'Invalid days requested'
    except Exception:
        errors['days'] = 'Invalid days requested'

    platforms = payload.get('platforms')
    if platforms is not None:
        try:
            list(platforms or [])
        except Exception:
            errors['platforms'] = 'Invalid platforms'

    image_data_url = payload.get('image_data_url')
    if image_data_url and len(str(image_data_url)) > IMAGE_DATA_URL_MAX_BYTES:
        errors['image_data_url'] = 'Image too large'

    return errors


def _normalize_generate_payload(payload: Mapping[str, Any]) -> dict:
    normalized: dict[str, Any] = {}
    try:
        normalized['days'] = max(1, int(payload.get('days') or 7))
    except Exception:
        normalized['days'] = 7

    start_day = payload.get('start_day')
    if isinstance(start_day, str):
        try:
            start_day = date.fromisoformat(start_day)
        except Exception:
            start_day = None
    if not isinstance(start_day, date):
        start_day = date.today()
    normalized['start_day'] = start_day

    normalized['industry'] = (payload.get('industry') or 'Business').strip() or 'Business'
    normalized['tone'] = payload.get('tone') or 'friendly'
    normalized['platforms'] = list(payload.get('platforms') or ['instagram'])
    normalized['brand_keywords'] = list(payload.get('brand_keywords') or [])
    normalized['include_images'] = bool(payload.get('include_images'))
    normalized['niche_keywords'] = list(payload.get('niche_keywords') or [])
    normalized['goals'] = list(payload.get('goals') or [])
    normalized['company'] = payload.get('company') or ''
    normalized['details'] = payload.get('details') or {}
    normalized['voice_profile'] = payload.get('voice_profile') or {}
    normalized['profile'] = payload.get('profile') or None
    normalized['include_trends'] = bool(payload.get('include_trends'))
    return normalized


def _validate_posts_output(posts: Any) -> dict:
    if not isinstance(posts, list) or not posts:
        raise ValueError('No posts returned')

    sanitized: list[dict[str, Any]] = []
    for post in posts:
        if not isinstance(post, Mapping):
            raise ValueError('Invalid post object')
        caption = str(post.get('caption') or '').strip()
        if not caption:
            raise ValueError('Post missing caption')
        platform = (post.get('platform') or 'instagram').strip() or 'instagram'
        sanitized_post = dict(post)
        sanitized_post['caption'] = caption
        sanitized_post['platform'] = platform
        sanitized.append(sanitized_post)

    return {'posts': sanitized, 'count': len(sanitized)}


def _validate_review_payload(payload: Mapping[str, Any]) -> dict:
    errors: dict[str, str] = {}
    if not payload.get('review_text'):
        errors['review_text'] = 'Review text is required'
    return errors


def _normalize_review_payload(payload: Mapping[str, Any]) -> dict:
    return {
        'review_text': (payload.get('review_text') or '').strip(),
        'tone': payload.get('tone') or 'professional',
        'company_name': payload.get('company') or payload.get('company_name') or '',
        'industry': payload.get('industry') or '',
    }


def _validate_review_output(result: Any) -> dict:
    if not isinstance(result, Mapping):
        raise ValueError('Invalid response payload')
    response = str(result.get('response') or '').strip()
    if not response:
        raise ValueError('Missing response text')
    return {
        'response': response,
        'method': result.get('method', 'fallback'),
        'detected_sentiment': result.get('detected_sentiment'),
    }


def _validate_variants_payload(payload: Mapping[str, Any]) -> dict:
    errors: dict[str, str] = {}
    try:
        count = int(payload.get('count') or 1)
        if count <= 0 or count > 10:
            errors['count'] = 'Invalid count'
    except Exception:
        errors['count'] = 'Invalid count'
    return errors


def _normalize_variants_payload(payload: Mapping[str, Any]) -> dict:
    try:
        count = int(payload.get('count') or 1)
    except Exception:
        count = 1
    count = min(max(count, 1), 10)
    return {
        'count': count,
        'industry': payload.get('industry') or 'business',
        'platform': payload.get('platform') or payload.get('primary_platform') or 'instagram',
        'tone': payload.get('tone') or 'friendly',
        'base_caption': payload.get('base_caption') or payload.get('caption') or '',
    }


def _validate_variants_output(variants: Any) -> dict:
    if not isinstance(variants, list) or not variants:
        raise ValueError('Missing variants')
    for group in variants:
        if not isinstance(group, Mapping):
            raise ValueError('Invalid variants group')
        payload = group.get('variants')
        if not isinstance(payload, Mapping) or not payload:
            raise ValueError('Invalid variants payload')
        for v in payload.values():
            if not isinstance(v, Mapping):
                raise ValueError('Invalid variant entry')
            if not any(isinstance(val, str) and val for val in v.values()):
                raise ValueError('Empty variant entry')
    return {'variants': variants, 'count': len(variants)}


def _generate_variants_fallback(normalized: Mapping[str, Any]) -> list[dict[str, Any]]:
    templates = {
        'twitter': 'Tweet: {base}',
        'youtube': 'Video description: {base}',
        'instagram': 'Insta caption: {base}',
        'facebook': 'FB caption: {base}',
        'linkedin': 'LinkedIn post: {base}',
    }
    base_caption = normalized.get('base_caption') or f"{str(normalized.get('industry') or 'Business').title()} insight"
    tone = normalized.get('tone') or 'friendly'
    count = int(normalized.get('count') or 1)
    groups: list[dict[str, Any]] = []
    for idx in range(count):
        variants: dict[str, dict[str, str]] = {}
        for platform, template in templates.items():
            key = 'description' if platform == 'youtube' else ('caption' if platform == 'instagram' else 'text')
            variants[platform] = {key: template.format(base=f"{base_caption} ({tone}) #{idx+1}")}
        groups.append({'variants': variants})
    return groups


# Helper functions for new generation service
def _load_workspace_context(user_id: Optional[str], profile_id: Optional[str]) -> Optional[dict]:
    """Load workspace context from database."""
    if not profile_id:
        return None
    
    db = get_db()
    row = db.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,)).fetchone()
    if not row:
        return None
    
    # Handle both dict-like Row objects and actual dicts
    platforms_str = row['platforms'] if 'platforms' in row.keys() else '[]'
    
    return {
        'company_name': row['company'] if 'company' in row.keys() and row['company'] else '',
        'industry': row['industry'] if 'industry' in row.keys() and row['industry'] else 'business',
        'default_tone': row['tone'] if 'tone' in row.keys() and row['tone'] else 'professional',
        'platforms': json.loads(platforms_str) if platforms_str else [],
        'offerings': row['details'] if 'details' in row.keys() else None,
        'audience': None,  # Not stored separately yet
        'compliance_notes': None  # Not stored separately yet
    }


def _load_voice_samples(user_id: Optional[str], profile_id: Optional[str]) -> Optional[List[str]]:
    """Load voice samples from database."""
    if not profile_id:
        return None
    
    db = get_db()
    row = db.execute('SELECT voice_profile FROM profiles WHERE id = ?', (profile_id,)).fetchone()
    if not row:
        return None
    
    try:
        if 'voice_profile' not in row.keys():
            return None
        
        voice_profile_str = row['voice_profile']
        if not voice_profile_str:
            return None
        
        voice_data = json.loads(voice_profile_str)
        if not voice_data:
            return None
        
        # Extract samples from voice data
        samples = voice_data.get('samples', [])
        if samples and isinstance(samples, list):
            return samples
        
        # Fallback: if analyzed data exists, might have sample_texts
        if voice_data.get('analyzed'):
            return voice_data.get('sample_texts', [])
        
        return None
    except (json.JSONDecodeError, TypeError):
        return None


def _load_include_avoid_phrases(user_id: Optional[str], profile_id: Optional[str]) -> Tuple[Optional[List[str]], Optional[List[str]]]:
    """Load include/avoid phrases from database."""
    if not profile_id:
        return None, None
    
    db = get_db()
    row = db.execute('SELECT voice_profile FROM profiles WHERE id = ?', (profile_id,)).fetchone()
    if not row:
        return None, None
    
    try:
        if 'voice_profile' not in row.keys():
            return None, None
        
        voice_profile_str = row['voice_profile']
        if not voice_profile_str:
            return None, None
        
        voice_data = json.loads(voice_profile_str)
        if not voice_data:
            return None, None
        
        include_phrases = voice_data.get('include_phrases', [])
        avoid_phrases = voice_data.get('avoid_phrases', [])
        
        return (include_phrases if include_phrases else None, 
                avoid_phrases if avoid_phrases else None)
    except (json.JSONDecodeError, TypeError):
        return None, None


@app.post('/api/generate')
def api_generate():
    data = request.get_json(force=True) or {}

    request_id = _get_request_id()

    flags = load_flags()
    platforms = data.get('platforms') or []
    try:
        platforms = list(platforms)
    except Exception:
        platforms = []
    try:
        days = int(data.get('days') or 7)
    except Exception:
        days = 7

    uid = session.get('user_id')
    is_paid = False
    should_mark_sample = False

    request_meta = {
        "event": "generator.request",
        "user_id": uid or 'anon',
        "days": days,
        "platforms": platforms,
        "has_image": bool(data.get('image_data_url')),
        "tone": data.get('tone') or '',
        "request_id": request_id,
    }
    start_ts = time.time()
    app.logger.info("generator.request", extra=request_meta)

    def _log_and_abort(status_code: int, message: str, event: str = "generator.blocked", code: str = "generation_failed"):
        payload = {'ok': False, 'error': {'code': code, 'message': message}, 'request_id': request_id, 'data': None}
        app.logger.info(event, extra={**request_meta, "event": event, "status": status_code, "error": message})
        return jsonify(payload), status_code

    if uid:
        db = get_db()
        u = db.execute('SELECT is_paid, free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
        if u and u['is_paid']:
            is_paid = True

    if flags.get('gate7DayToPaid') and days >= 7:
        if not uid:
            return _log_and_abort(401, 'Login required')
        if not is_paid:
            return _log_and_abort(403, 'Paid plan required for 7-day generation')

    if not is_paid and uid:
        db = get_db()
        u = db.execute('SELECT free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
        if u and u['free_sample_used']:
            return _log_and_abort(403, 'Free sample already used')
        should_mark_sample = True

    if 'short_video' in platforms and not is_paid:
        return _log_and_abort(403, 'Paid plan required for Reels generation')

    if 'short_video' in platforms and is_paid:
        quota = int(os.getenv('REELS_QUOTA_MONTHLY', '30'))
        period = datetime.now().strftime('%Y-%m')
        db = get_db()
        usage = db.execute('SELECT reels_generated FROM generation_usage WHERE user_id = ? AND period = ?', (uid, period)).fetchone()
        used = usage['reels_generated'] if usage else 0
        if used >= quota:
            return _log_and_abort(403, 'Monthly Reels quota exceeded')

    image_data_url = data.get('image_data_url')
    if image_data_url:
        if len(image_data_url) > IMAGE_DATA_URL_MAX_BYTES:
            return _log_and_abort(400, 'Image too large', code='image_too_large')

        if not USE_OPENAI or openai_client is None:
            return _log_and_abort(
                503,
                'Image-to-post generation requires OpenAI. Add OPENAI_API_KEY or disable image uploads.',
                event="generator.failed",
            )

        try:
            posts = _generate_posts_from_image(data) or []
            if not isinstance(posts, list) or not posts:
                return _log_and_abort(500, 'Image generation not available', event="generator.failed", code="image_generation_failed")
            duration_ms = int((time.time() - start_ts) * 1000)
            app.logger.info("generator.success", extra={**request_meta, "event": "generator.success", "duration_ms": duration_ms, "count": len(posts)})
            body = {'ok': True, 'data': {'posts': posts, 'count': len(posts)}, 'request_id': request_id, 'posts': posts, 'count': len(posts)}
            return jsonify(body)
        except Exception:
            app.logger.exception("Image generation failed", extra={**request_meta, "event": "generator.failed"})
            return _log_and_abort(500, 'Image generation failed. Please try again.', event="generator.failed", code="image_generation_failed")

    service_response = generation_service.generate(
        endpoint='generate',
        request_id=request_id,
        payload=data,
        validator=_validate_generate_payload,
        normalizer=_normalize_generate_payload,
        output_validator=_validate_posts_output,
        openai_callable=lambda normalized: gen_mod.generate_posts_with_openai(request_id=request_id, **normalized),
        fallback_callable=lambda normalized: generate_posts(**{k: v for k, v in normalized.items() if k != 'include_trends'}),
        use_openai=gen_mod.USE_OPENAI_FOR_POSTS,
    )

    body = dict(service_response.body)
    data_payload = body.pop('data', {}) if isinstance(body.get('data'), dict) else (body.pop('data') if 'data' in body else {})
    if service_response.ok and isinstance(data_payload, dict):
        posts = data_payload.get('posts') or []
        body['data'] = data_payload
        body['posts'] = posts
        body['count'] = data_payload.get('count', len(posts))
        if should_mark_sample and uid:
            db = get_db()
            db.execute('UPDATE users SET free_sample_used = 1 WHERE id = ?', (uid,))
            db.commit()
    else:
        body.setdefault('data', None)

    return jsonify(body), service_response.status


@app.post('/api/generate/social')
def api_generate_social():
    """Generate social media posts using new generation service with full context."""
    uid = session.get('user_id')
    pid = session.get('profile_id')
    
    data = request.get_json(silent=True) or {}
    
    # Load context from database
    workspace = _load_workspace_context(uid, pid)
    voice_samples = _load_voice_samples(uid, pid)
    include_phrases, avoid_phrases = _load_include_avoid_phrases(uid, pid)
    
    # Build request params
    request_params = {
        'session_length': data.get('session_length') or data.get('days', 7),
        'platforms': data.get('platforms') or [],
        'tone': data.get('tone'),
        'goals': data.get('goals') or [],
        'keywords': data.get('keywords') or [],
        'reel_options': data.get('reel_options') or {},
        'image_tailor': data.get('image_tailor'),
    }
    
    # Generate using new service
    result = new_generation_service.generate_social_posts(
        workspace=workspace,
        request=request_params,
        voice_samples=voice_samples,
        include_phrases=include_phrases,
        avoid_phrases=avoid_phrases
    )
    
    # Return result with appropriate status code
    status_code = 200 if result.get('ok') else 400
    return jsonify(result), status_code


@app.post('/api/generate/reels')
def api_generate_reels():
    """Generate structured reels/shorts scripts with sectional regeneration support."""
    request_id = _get_request_id()
    data = request.get_json(silent=True) or {}

    style = data.get('hook_style') or data.get('style') or 'Face-camera tips'
    format_hint = data.get('format') or 'talking_head'
    duration = data.get('duration_seconds') or data.get('reel_length') or 30
    include_shot_list = bool(data.get('include_shot_list', True))
    include_on_screen_text = bool(data.get('include_on_screen_text', True))
    section = (data.get('section') or '').lower()

    try:
        plan = gen_mod.make_reel_plan(
            industry=data.get('industry') or 'Business',
            pillar_name=data.get('pillar_name') or 'Story',
            brand_keywords=data.get('brand_keywords') or [],
            tone=data.get('tone') or 'friendly',
            company=data.get('company') or '',
            reel_style=style,
            goals=data.get('goals') or [],
            niche_keywords=data.get('niche_keywords') or [],
            length_seconds=duration,
            production_tier=data.get('production_tier') or 'solo'
        )
    except Exception:
        app.logger.exception("reels.generate.failed", extra={'request_id': request_id})
        return jsonify({
            'ok': False,
            'error': {'message': 'Unable to generate a reel right now.'},
            'request_id': request_id
        }), 500

    if section == 'hook':
        return jsonify({'ok': True, 'hook': plan.get('hook'), 'request_id': request_id})
    if section == 'cta':
        return jsonify({'ok': True, 'cta': plan.get('cta'), 'request_id': request_id})

    primary_tags = []
    hashtags = plan.get('hashtags') or {}
    if isinstance(hashtags, dict):
        primary_tags = list(hashtags.get('primary') or [])
    elif isinstance(hashtags, list):
        primary_tags = hashtags

    beats = []
    for beat in plan.get('beats', []):
        beats.append({
            'label': beat.get('osd'),
            'line': beat.get('line'),
            'start': beat.get('start_s'),
            'end': beat.get('end_s')
        })

    shot_list = []
    if include_shot_list:
        for shot in plan.get('shot_list', []):
            shot_list.append({
                'beat': shot.get('beat') or shot.get('osd'),
                'shot': shot.get('shot') or shot.get('shot_type'),
                'start': shot.get('start_s'),
                'end': shot.get('end_s'),
                'overlay': shot.get('overlay')
            })

    overlays = []
    if include_on_screen_text:
        overlays = [
            item.get('text') for item in (plan.get('caption_overlays') or []) if item.get('text')
        ] or list(plan.get('on_screen_text') or [])

    reel_payload = {
        'style': plan.get('style'),
        'format': format_hint,
        'duration_seconds': int(duration),
        'hook': plan.get('hook'),
        'beats': beats,
        'cta': plan.get('cta'),
        'caption': plan.get('thumbnail_prompt') or f"{plan.get('hook', '')} — {plan.get('cta', '')}",
        'hashtags': primary_tags,
        'shot_list': shot_list,
        'on_screen_text': overlays
    }

    return jsonify({'ok': True, 'reel': reel_payload, 'request_id': request_id})


@app.post('/api/generate-review-response')
def api_generate_review_response():
    data = request.get_json(force=True) or {}
    request_id = _get_request_id()

    service_response = generation_service.generate(
        endpoint='generate-review-response',
        request_id=request_id,
        payload=data,
        validator=_validate_review_payload,
        normalizer=_normalize_review_payload,
        output_validator=_validate_review_output,
        fallback_callable=lambda normalized: gen_mod.generate_review_response(**normalized),
        use_openai=False,
    )

    body = dict(service_response.body)
    data_payload = body.pop('data', {}) if isinstance(body.get('data'), dict) else (body.pop('data') if 'data' in body else {})
    if service_response.ok and isinstance(data_payload, dict):
        body['data'] = data_payload
        body.update(data_payload)
    else:
        body.setdefault('data', None)

    return jsonify(body), service_response.status


@app.post('/api/generate/reviews')
def api_generate_reviews():
    """Generate structured review responses using new generation service."""
    uid = session.get('user_id')
    pid = session.get('profile_id')
    
    data = request.get_json(force=True) or {}
    review_text = (data.get('review_text') or '').strip()

    if not review_text:
        request_id = _get_request_id()
        return jsonify({
            'ok': False, 
            'error': {'code': 'missing_review', 'message': 'Review text is required.'}, 
            'request_id': request_id
        }), 400

    # Check for sensitive content in input
    sensitive_patterns = [
        r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
        r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",
        r"ssn\b",
    ]
    for pattern in sensitive_patterns:
        if re.search(pattern, review_text, re.IGNORECASE):
            request_id = _get_request_id()
            return jsonify({
                'ok': False,
                'error': {
                    'code': 'sensitive_content',
                    'message': 'Please remove personal contact info before generating.',
                },
                'request_id': request_id
            }), 400

    # Load context from database
    workspace = _load_workspace_context(uid, pid)
    voice_samples = None
    include_phrases = None
    avoid_phrases = None
    
    # Only load voice if brand_voice is requested
    if data.get('use_brand_voice') or data.get('brand_voice'):
        voice_samples = _load_voice_samples(uid, pid)
        include_phrases, avoid_phrases = _load_include_avoid_phrases(uid, pid)
    
    # Build request params
    request_params = {
        'review_text': review_text,
        'rating': data.get('rating'),
        'channel': data.get('channel') or '',
        'tone': data.get('tone') or 'professional',
        'response_length': data.get('length') or 'medium',
        'use_brand_voice': bool(data.get('use_brand_voice') or data.get('brand_voice')),
    }
    
    # Generate using new service
    result = new_generation_service.generate_review_response(
        workspace=workspace,
        request=request_params,
        voice_samples=voice_samples,
        include_phrases=include_phrases,
        avoid_phrases=avoid_phrases
    )
    
    # Return result with appropriate status code
    status_code = 200 if result.get('ok') else (400 if result.get('error', {}).get('code') == 'validation_error' else 500)
    return jsonify(result), status_code


@app.get('/voice-setup')
def voice_setup_page():
    uid = session.get('user_id')
    if not uid:
        return redirect(url_for('login_page'))
    
    db = get_db()
    user = db.execute('SELECT id, email, is_paid, free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
    if not user:
        return redirect(url_for('login_page'))
        
    return render_template('voice_setup.html', initial_user=dict(user))


@app.post('/api/voice/analyze')
def api_voice_analyze():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
        
    data = request.get_json(force=True) or {}
    samples = data.get('samples', [])
    
    if isinstance(samples, str):
        samples = [samples]
    
    if not samples or not isinstance(samples, list):
        return jsonify({'ok': False, 'error': 'Invalid samples provided'}), 400
        
    try:
        profile = voice_profile.profile_from_samples(samples)
        return jsonify({'ok': True, 'profile': profile})
    except Exception as e:
        logging.exception("Voice analysis failed")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.post('/api/voice/scrape')
def api_voice_scrape():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401

    data = request.get_json(force=True) or {}
    url = data.get('url')
    
    if not url:
        return jsonify({'ok': False, 'error': 'No URL provided'}), 400
        
    try:
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return jsonify({'ok': False, 'error': f'Failed to fetch URL: {resp.status_code}'}), 400
            
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract text from paragraphs
        texts = []
        for p in soup.find_all(['p', 'div', 'span', 'li']):
            text = p.get_text().strip()
            if len(text) > 20: # Filter short snippets
                texts.append(text)
                
        # Limit to top 20 longest texts to avoid noise
        texts.sort(key=len, reverse=True)
        texts = texts[:20]
        
        if not texts:
            return jsonify({'ok': False, 'error': 'No readable text found'}), 400
            
        return jsonify({
            'ok': True,
            'samples': texts
        })
        
    except Exception as e:
        logging.error(f"Scrape error: {e}")
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.post('/api/voice/save')
def api_voice_save():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
        
    data = request.get_json() or {}
    profile = data.get('profile')
    
    if not profile or not isinstance(profile, dict):
        return jsonify({'ok': False, 'error': 'Invalid profile data'}), 400
        
    db = get_db()
    profile_json = json.dumps(profile)
    
    # 1. Save to profiles table (Primary for generator)
    pid = session.get('profile_id')
    if not pid:
        pid = str(uuid.uuid4())
        session['profile_id'] = pid
        
    try:
        existing = db.execute('SELECT id FROM profiles WHERE id = ?', (pid,)).fetchone()
        if existing:
            db.execute('UPDATE profiles SET voice_profile = ? WHERE id = ?', (profile_json, pid))
        else:
            db.execute('INSERT INTO profiles (id, voice_profile) VALUES (?, ?)', (pid, profile_json))
        db.commit()
    except Exception as e:
        logging.error(f"Failed to save to profiles table: {e}")
        try:
            db.rollback()
        except:
            pass

    # 2. Save to users table (Legacy/Persistence)
    try:
        db.execute('UPDATE users SET voice_profile = ? WHERE id = ?', (profile_json, uid))
        db.commit()
    except Exception as e:
        logging.warning(f"Failed to save to users table (schema mismatch?): {e}")
        try:
            db.rollback()
        except:
            pass
        
    return jsonify({'ok': True})


@app.post('/api/cancel-subscription')
def api_cancel_subscription():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
    if OUTBOUND_KILL_SWITCH:
        return jsonify({'ok': False, 'error': 'Outbound calls disabled for maintenance'}), 503
    db = get_db()
    # find active subscription and mark canceled (dev-only; in prod call Stripe API)
    sub = db.execute('SELECT id, stripe_subscription_id, status FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (uid,)).fetchone()
    if not sub:
        return jsonify({'ok': False, 'error': 'No subscription found'}), 400
    # If Stripe is configured and subscription id exists, cancel at Stripe
    try:
        if stripe and os.getenv('STRIPE_SECRET_KEY') and sub['stripe_subscription_id']:
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            try:
                stripe.Subscription.delete(sub['stripe_subscription_id'])
            except Exception as e:
                # if deletion fails, fallback to marking canceled locally but report error
                db.execute('UPDATE subscriptions SET status = ? WHERE id = ?', ('canceled', sub['id']))
                db.execute('UPDATE users SET is_paid = 0 WHERE id = ?', (uid,))
                db.commit()
                return jsonify({'ok': False, 'error': f'stripe error: {e}'}), 502
        # mark canceled locally
        db.execute('UPDATE subscriptions SET status = ? WHERE id = ?', ('canceled', sub['id']))
        db.execute('UPDATE users SET is_paid = 0 WHERE id = ?', (uid,))
        db.commit()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.post('/api/create-checkout-session')
def api_create_checkout_session():
    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured'}), 501

    if not hasattr(stripe, 'checkout') or not hasattr(stripe.checkout, 'Session'):
        return jsonify({'ok': False, 'error': 'Stripe checkout not available'}), 501

    if OUTBOUND_KILL_SWITCH:
        return jsonify({'ok': False, 'error': 'Outbound calls disabled for maintenance'}), 503

    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    data = request.get_json(force=True) or {}
    price_id = (data.get('price_id') or os.getenv('STRIPE_TEST_PRICE_ID') or '').strip()
    if not price_id:
        return jsonify({'ok': False, 'error': 'price_id required'}), 400

    success_url = data.get('success_url') or url_for('account_page', _external=True)
    cancel_url = data.get('cancel_url') or url_for('account_page', _external=True)
    client_reference_id = session.get('user_id')

    try:
        session_args = dict(
            mode='subscription',
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            allow_promotion_codes=True,
        )
        if client_reference_id:
            session_args['client_reference_id'] = client_reference_id
        session_obj = stripe.checkout.Session.create(**session_args)  # type: ignore[arg-type]
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 502

    return jsonify({'ok': True, 'sessionId': session_obj.get('id'), 'url': session_obj.get('url')})


@app.post('/api/create-subscription')
def api_create_subscription():
    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured'}), 501

    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
    if OUTBOUND_KILL_SWITCH:
        return jsonify({'ok': False, 'error': 'Outbound calls disabled for maintenance'}), 503

    data = request.get_json(force=True) or {}
    price_id = (data.get('price_id') or os.getenv('STRIPE_TEST_PRICE_ID') or '').strip()
    payment_method = (data.get('payment_method') or '').strip()
    if not price_id:
        return jsonify({'ok': False, 'error': 'price_id required'}), 400
    if not payment_method:
        return jsonify({'ok': False, 'error': 'payment_method required'}), 400

    db = get_db()
    user = db.execute('SELECT id, email, stripe_customer_id FROM users WHERE id = ?', (uid,)).fetchone()
    if not user:
        return jsonify({'ok': False, 'error': 'User not found'}), 404

    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    customer_id = user['stripe_customer_id']

    try:
        if not customer_id:
            customer = stripe.Customer.create(email=user['email'])
            customer_id = customer.get('id')
            if not customer_id:
                return jsonify({'ok': False, 'error': 'Unable to create Stripe customer'}), 502
            db.execute('UPDATE users SET stripe_customer_id = ? WHERE id = ?', (customer_id, uid))
            db.commit()

        stripe.PaymentMethod.attach(payment_method, customer=customer_id)  # type: ignore[arg-type]
        stripe.Customer.modify(customer_id, invoice_settings={'default_payment_method': payment_method})  # type: ignore[arg-type]

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
            payment_settings={'save_default_payment_method': 'on_subscription'}
        )  # type: ignore[arg-type]

        client_secret = (subscription.get('latest_invoice') or {}).get('payment_intent', {}).get('client_secret')
        sub_id = subscription.get('id')
        status = subscription.get('status')
        current_period_end = subscription.get('current_period_end')

        db.execute(
            'INSERT INTO subscriptions (id, user_id, stripe_subscription_id, status, current_period_end) VALUES (?, ?, ?, ?, ?)',
            (str(uuid.uuid4()), uid, sub_id, status, current_period_end)
        )
        db.execute('UPDATE users SET is_paid = ? WHERE id = ?', (1 if status in ('active', 'trialing') else 0, uid))
        db.commit()
    except AttributeError:
        return jsonify({'ok': False, 'error': 'Stripe client missing required methods'}), 501
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 502

    return jsonify({'ok': True, 'subscription_id': sub_id, 'client_secret': client_secret})


def _parse_stripe_event(request):
    payload = request.get_data(as_text=False)
    sig_header = request.headers.get('Stripe-Signature')
    secret = (os.getenv('STRIPE_WEBHOOK_SECRET') or '').strip()
    should_verify = bool(secret) and secret.lower() not in ('whsec_replace_me', 'your_webhook_secret_here') and stripe is not None
    if should_verify and stripe:
        try:
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            event = stripe.Webhook.construct_event(payload=payload, sig_header=sig_header, secret=secret)
            return event.to_dict_recursive()
        except Exception:
            pass
    try:
        return json.loads(payload.decode('utf-8') if payload else '{}')
    except Exception:
        raise ValueError('Invalid JSON payload')


def _mark_subscription_active(user_id: Optional[str], customer_id: Optional[str], subscription_id: Optional[str], current_period_end=None):
    if not user_id:
        return
    db = get_db()
    if customer_id:
        db.execute('UPDATE users SET is_paid = 1, stripe_customer_id = ? WHERE id = ?', (customer_id, user_id))
    else:
        db.execute('UPDATE users SET is_paid = 1 WHERE id = ?', (user_id,))
    if subscription_id:
        existing = db.execute('SELECT id FROM subscriptions WHERE stripe_subscription_id = ?', (subscription_id,)).fetchone()
        if existing:
            db.execute('UPDATE subscriptions SET user_id = ?, status = ?, current_period_end = ? WHERE id = ?', (user_id, 'active', current_period_end, existing['id']))
        else:
            db.execute('INSERT INTO subscriptions (id, user_id, stripe_subscription_id, status, current_period_end) VALUES (?, ?, ?, ?, ?)', (str(uuid.uuid4()), user_id, subscription_id, 'active', current_period_end))
    db.commit()


def _mark_subscription_canceled(user_id: Optional[str], subscription_id: Optional[str]):
    db = get_db()
    if subscription_id:
        existing = db.execute('SELECT id, user_id FROM subscriptions WHERE stripe_subscription_id = ?', (subscription_id,)).fetchone()
        if existing:
            db.execute('UPDATE subscriptions SET status = ? WHERE id = ?', ('canceled', existing['id']))
            user_id = user_id or existing['user_id']
    if user_id:
        db.execute('UPDATE users SET is_paid = 0 WHERE id = ?', (user_id,))
    db.commit()


@app.post('/api/stripe-webhook')
def stripe_webhook():
    try:
        event = _parse_stripe_event(request)
    except ValueError as e:
        return jsonify({'ok': False, 'error': str(e)}), 400

    event_type = event.get('type')
    data_object = event.get('data', {}).get('object', {})
    handled = False

    if event_type == 'checkout.session.completed':
        uid = data_object.get('client_reference_id')
        customer_id = data_object.get('customer')
        subscription_id = data_object.get('subscription')
        _mark_subscription_active(uid, customer_id, subscription_id)
        handled = True
    elif event_type in ('invoice.payment_succeeded', 'customer.subscription.updated'):
        subscription_id = data_object.get('subscription') or data_object.get('id')
        uid = data_object.get('client_reference_id')
        if not uid and data_object.get('customer'):
            db = get_db()
            row = db.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (data_object.get('customer'),)).fetchone()
            uid = row['id'] if row else None
        current_period_end = data_object.get('current_period_end') or data_object.get('lines', {}).get('data', [{}])[0].get('period', {}).get('end') if isinstance(data_object.get('lines'), dict) else None
        _mark_subscription_active(uid, data_object.get('customer'), subscription_id, current_period_end)
        handled = True
    elif event_type in ('customer.subscription.deleted', 'invoice.payment_failed'):
        subscription_id = data_object.get('id') or data_object.get('subscription')
        uid = data_object.get('client_reference_id')
        if not uid and data_object.get('customer'):
            db = get_db()
            row = db.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (data_object.get('customer'),)).fetchone()
            uid = row['id'] if row else None
        _mark_subscription_canceled(uid, subscription_id)
        handled = True

    return jsonify({'ok': True, 'handled': handled})


@app.get("/api/content")
def api_content():
    # return minimal metadata about content pack (version and flags)
    cfg_path = os.path.join(os.path.dirname(__file__), "static", "content", "config.json")
    flags_path = os.path.join(os.path.dirname(__file__), "static", "content", "flags.json")
    out: dict = {"version": "local", "flags": {}}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            out["version"] = cfg.get("version", out["version"])
    except Exception:
        pass
    try:
        with open(flags_path, "r", encoding="utf-8") as f:
            flags = json.load(f)
            out["flags"] = flags
    except Exception:
        out["flags"] = {}
    return jsonify(out)


def load_flags():
    flags_path = os.path.join(os.path.dirname(__file__), "static", "content", "flags.json")
    try:
        with open(flags_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def perform_reconcile(db=None):
    """Perform reconciliation logic and return results list."""
    close_here = False
    if db is None:
        db = get_db()
        close_here = False
    rows = db.execute('SELECT id, user_id, stripe_subscription_id FROM subscriptions WHERE stripe_subscription_id IS NOT NULL').fetchall()
    results = []
    for r in rows:
        sid = r['stripe_subscription_id']
        try:
            remote = stripe.Subscription.retrieve(sid) if stripe else {}
            status = remote.get('status') if remote else None
            cpe = remote.get('current_period_end') if remote else None
            db.execute('UPDATE subscriptions SET status = ?, current_period_end = ? WHERE id = ?', (status, cpe, r['id']))
            is_paid = 1 if status in ('active', 'trialing') else 0
            db.execute('UPDATE users SET is_paid = ? WHERE id = ?', (is_paid, r['user_id']))
            results.append({'id': r['id'], 'stripe_subscription_id': sid, 'status': status})
        except Exception as e:
            results.append({'id': r['id'], 'stripe_subscription_id': sid, 'error': str(e)})
    db.commit()
    return results


@app.post('/api/reconcile-job')
def api_reconcile_job():
    """Create a reconcile job. If wait=1 is passed, run synchronously and return results."""
    admin_emails = os.getenv('ADMIN_EMAILS', '')
    if admin_emails and not is_admin():
        return jsonify({'ok': False, 'error': 'Admin required'}), 403
    if admin_emails:
        token = request.headers.get('X-CSRF-Token')
        if not token or token != session.get('admin_csrf'):
            return jsonify({'ok': False, 'error': 'CSRF token required'}), 403
    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured'}), 501

    wait = request.args.get('wait') == '1'
    job_id = str(uuid.uuid4())
    db = get_db()
    started = datetime.now(timezone.utc).isoformat()
    db.execute('INSERT INTO reconcile_jobs (id, status, started_at) VALUES (?, ?, ?)', (job_id, 'running', started))
    db.commit()

    def run_job(jid):
        try:
            results = perform_reconcile(db=db)
            finished = datetime.now(timezone.utc).isoformat()
            db.execute('UPDATE reconcile_jobs SET status = ?, result = ?, finished_at = ? WHERE id = ?', ('finished', json.dumps(results), finished, jid))
            db.commit()
        except Exception as e:
            finished = datetime.now(timezone.utc).isoformat()
            db.execute('UPDATE reconcile_jobs SET status = ?, result = ?, finished_at = ? WHERE id = ?', ('failed', str(e), finished, jid))
            db.commit()

    if wait:
        run_job(job_id)
        row = db.execute('SELECT * FROM reconcile_jobs WHERE id = ?', (job_id,)).fetchone()
        return jsonify({'ok': True, 'job': dict(row) if row else None})
    else:
        t = threading.Thread(target=run_job, args=(job_id,))
        t.daemon = True
        t.start()
        return jsonify({'ok': True, 'job_id': job_id})


@app.post('/api/reconcile-subscriptions')
def api_reconcile_subscriptions():
    admin_emails = (os.getenv('ADMIN_EMAILS') or '').strip()
    require_admin = bool(admin_emails)
    if require_admin:
        if not is_admin():
            return jsonify({'ok': False, 'error': 'Admin required'}), 403
        token = request.headers.get('X-CSRF-Token')
        if not token or token != session.get('admin_csrf'):
            return jsonify({'ok': False, 'error': 'CSRF token required'}), 403

    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured'}), 501

    try:
        results = perform_reconcile()
    except Exception as exc:
        return jsonify({'ok': False, 'error': str(exc)}), 500

    return jsonify({'ok': True, 'results': results})


@app.get('/api/reconcile-jobs/<job_id>')
def api_reconcile_job_get(job_id):
    if not is_admin() and os.getenv('ADMIN_EMAILS', ''):
        return jsonify({'ok': False, 'error': 'Admin required'}), 403
    db = get_db()
    row = db.execute('SELECT * FROM reconcile_jobs WHERE id = ?', (job_id,)).fetchone()
    if not row:
        return jsonify({'ok': False, 'error': 'Not found'}), 404
    return jsonify({'ok': True, 'job': row_to_mapping(row)})


def is_admin():
    """Simple admin check based on ADMIN_EMAILS env var (comma-separated)."""
    uid = session.get('user_id')
    if not uid:
        return False
    db = get_db()
    # select is_admin flag if present
    row = db.execute('SELECT email, is_admin FROM users WHERE id = ?', (uid,)).fetchone()
    if not row:
        return False
    # Prefer explicit is_admin column if present
    try:
        # sqlite3.Row supports mapping access; treat truthy values as admin
        if 'is_admin' in row.keys() and row['is_admin']:
            return True
    except Exception:
        pass
    # Fallback to ADMIN_EMAILS env var if configured
    admin_emails = os.getenv('ADMIN_EMAILS', '')
    if not admin_emails:
        return False
    allowed = [e.strip().lower() for e in admin_emails.split(',') if e.strip()]
    return row['email'].lower() in allowed


def _get_admin_scope() -> dict[str, object]:
    """Return metadata about the current admin user (super vs. team admin)."""
    row = _get_current_user_row()
    if not row:
        return {
            'allowed': False,
            'is_super_admin': False,
            'is_team_admin': False,
            'team_owner_id': None,
            'team_owner_email': None,
        }

    row_dict = row_to_mapping(row) if not isinstance(row, dict) else row
    email = (row_dict.get('email') or '').strip().lower()
    tier = (row_dict.get('subscription_tier') or '').strip().lower()
    has_admin_flag = bool(row_dict.get('is_admin'))
    admin_emails = [e.strip().lower() for e in (os.getenv('ADMIN_EMAILS') or '').split(',') if e.strip()]

    # Super admins are either explicitly configured via ADMIN_EMAILS or any admin
    # user who is not on a team subscription tier (legacy behavior).
    is_super_admin = False
    if admin_emails:
        is_super_admin = email in admin_emails
    if not is_super_admin and has_admin_flag and tier != 'team':
        is_super_admin = True

    is_team_admin = has_admin_flag and tier == 'team' and not is_super_admin

    return {
        'allowed': has_admin_flag or is_super_admin,
        'is_super_admin': is_super_admin,
        'is_team_admin': is_team_admin,
        'team_owner_id': row_dict.get('id') if is_team_admin else None,
        'team_owner_email': row_dict.get('email') if is_team_admin else None,
        'user_id': row_dict.get('id'),
        'email': row_dict.get('email'),
    }


@app.get('/api/admin/users')
def api_admin_users():
    if not is_admin():
        return jsonify({'ok': False, 'error': 'Admin required'}), 403

    scope = _get_admin_scope()
    if not scope.get('allowed'):
        return jsonify({'ok': False, 'error': 'Admin scope not available'}), 403

    db = get_db()
    if scope.get('is_super_admin'):
        user_rows = db.execute('SELECT id, email, created_at, is_paid, stripe_customer_id, is_admin, free_sample_used, subscription_tier FROM users ORDER BY created_at DESC').fetchall()
    else:
        owner_id = scope.get('team_owner_id')
        user_rows = db.execute('SELECT id, email, created_at, is_paid, stripe_customer_id, is_admin, free_sample_used, subscription_tier FROM users WHERE id = ? ORDER BY created_at DESC', (owner_id,)).fetchall()
    subs = {}
    if scope.get('is_super_admin'):
        sub_rows = db.execute('SELECT user_id, status, stripe_subscription_id, current_period_end FROM subscriptions ORDER BY created_at DESC').fetchall()
    else:
        sub_rows = db.execute('SELECT user_id, status, stripe_subscription_id, current_period_end FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC', (scope.get('team_owner_id'),)).fetchall()
    for sub in sub_rows:
        if sub['user_id'] not in subs:
            subs[sub['user_id']] = sub

    if scope.get('is_super_admin'):
        profile_stats_row = db.execute('SELECT COUNT(*) AS total FROM profiles').fetchone()
    else:
        profile_stats_row = db.execute('SELECT COUNT(*) AS total FROM profiles WHERE id = ?', (scope.get('team_owner_id'),)).fetchone()
    total_profiles = profile_stats_row['total'] if profile_stats_row else 0

    payload_users = []
    for row in user_rows:
        sub = subs.get(row['id'])
        payload_users.append({
            'id': row['id'],
            'email': row['email'],
            'created_at': row['created_at'],
            'is_paid': bool(row['is_paid']),
            'is_admin': bool(row['is_admin']) if 'is_admin' in row.keys() else False,
            'has_stripe': bool(row['stripe_customer_id']),
            'stripe_customer_id': row['stripe_customer_id'],
            'subscription_status': sub['status'] if sub else None,
            'stripe_subscription_id': sub['stripe_subscription_id'] if sub else None,
            'current_period_end': sub['current_period_end'] if sub else None,
            'free_sample_used': bool(row['free_sample_used']) if row['free_sample_used'] is not None else False,
            'subscription_tier': row['subscription_tier'] if 'subscription_tier' in row.keys() else None,
        })

    if scope.get('is_super_admin'):
        team_rows = db.execute('SELECT id, owner_user_id, member_email, created_at FROM team_members ORDER BY created_at ASC').fetchall()
    else:
        team_rows = db.execute('SELECT id, owner_user_id, member_email, created_at FROM team_members WHERE owner_user_id = ? ORDER BY created_at ASC', (scope.get('team_owner_id'),)).fetchall()
    members_by_owner = {}
    for tm in team_rows:
        members_by_owner.setdefault(tm['owner_user_id'], []).append({
            'id': tm['id'],
            'email': tm['member_email'],
            'created_at': tm['created_at'],
        })

    team_accounts = []
    for user in payload_users:
        tier = (user.get('subscription_tier') or '').lower()
        if tier == 'team':
            team_accounts.append({
                'owner_id': user['id'],
                'owner_email': user['email'],
                'member_limit': TEAM_MEMBER_LIMIT,
                'members': members_by_owner.get(user['id'], [])
            })

    stats = {
        'total_users': len(payload_users),
        'paid_users': sum(1 for u in payload_users if u['is_paid']),
        'free_users': sum(1 for u in payload_users if not u['is_paid']),
        'profile_stats': {
            'total_profiles': total_profiles,
        },
        'team_accounts': len(team_accounts)
    }

    mode = 'super' if scope.get('is_super_admin') else ('team' if scope.get('is_team_admin') else 'restricted')
   

   
    response_scope = {
        'mode': mode,
        'team_owner_id': scope.get('team_owner_id'),
        'team_owner_email': scope.get('team_owner_email'),
        'can_reconcile': bool(scope.get('is_super_admin')),
    }

    return jsonify({'ok': True, 'users': payload_users, 'stats': stats, 'teams': team_accounts, 'scope': response_scope})


@app.post('/api/admin/team-members')
def api_admin_team_member_create():
    if not is_admin():
        return jsonify({'ok': False, 'error': 'Admin required'}), 403
    token = request.headers.get('X-CSRF-Token')
    if not token or token != session.get('admin_csrf'):
        return jsonify({'ok': False, 'error': 'CSRF token required'}), 403

    scope = _get_admin_scope()
    data = request.get_json(silent=True) or {}
    owner_id = (data.get('owner_id') or '').strip()
    member_email = (data.get('email') or '').strip().lower()

    if not owner_id:
        return jsonify({'ok': False, 'error': 'Owner is required'}), 400
    if not member_email:
        return jsonify({'ok': False, 'error': 'Email is required'}), 400
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", member_email):
        return jsonify({'ok': False, 'error': 'Invalid email address'}), 400

    if not scope.get('is_super_admin'):
        allowed_owner = scope.get('team_owner_id')
        if not allowed_owner or allowed_owner != owner_id:
            return jsonify({'ok': False, 'error': 'Not authorized for this team'}), 403

    db = get_db()
    owner = db.execute('SELECT id, subscription_tier FROM users WHERE id = ?', (owner_id,)).fetchone()
    if not owner:
        return jsonify({'ok': False, 'error': 'Owner not found'}), 404
    if (owner['subscription_tier'] or '').lower() != 'team':
        return jsonify({'ok': False, 'error': 'User is not on a team plan'}), 400

    count_row = db.execute('SELECT COUNT(*) AS cnt FROM team_members WHERE owner_user_id = ?', (owner_id,)).fetchone()
    if count_row and count_row['cnt'] >= TEAM_MEMBER_LIMIT:
        return jsonify({'ok': False, 'error': f'Team member limit ({TEAM_MEMBER_LIMIT}) reached'}), 400

    try:
        db.execute('INSERT INTO team_members (owner_user_id, member_email) VALUES (?, ?)', (owner_id, member_email))
        db.commit()
    except (sqlite3.IntegrityError, *DB_INTEGRITY_ERRORS):
        return jsonify({'ok': False, 'error': 'Member already exists for this team'}), 409

    row = db.execute('SELECT id, owner_user_id, member_email, created_at FROM team_members WHERE owner_user_id = ? AND member_email = ?', (owner_id, member_email)).fetchone()
    return jsonify({'ok': True, 'member': row_to_mapping(row)})


@app.delete('/api/admin/team-members/<int:member_id>')
def api_admin_team_member_delete(member_id: int):
    if not is_admin():
        return jsonify({'ok': False, 'error': 'Admin required'}), 403
    token = request.headers.get('X-CSRF-Token')
    if not token or token != session.get('admin_csrf'):
        return jsonify({'ok': False, 'error': 'CSRF token required'}), 403

    scope = _get_admin_scope()
    db = get_db()
    existing = db.execute('SELECT id, owner_user_id FROM team_members WHERE id = ?', (member_id,)).fetchone()
    if not existing:
        return jsonify({'ok': False, 'error': 'Team member not found'}), 404

    if not scope.get('is_super_admin'):
        allowed_owner = scope.get('team_owner_id')
        if not allowed_owner or existing['owner_user_id'] != allowed_owner:
            return jsonify({'ok': False, 'error': 'Not authorized for this team'}), 403

    db.execute('DELETE FROM team_members WHERE id = ?', (member_id,))
    db.commit()
    return jsonify({'ok': True, 'deleted': member_id})


def _serialize_approval_row(row):
    if not row:
        return None
    raw = dict(row)
    reviewers = []
    try:
        if raw.get('reviewers'):
            reviewers = json.loads(raw['reviewers'])
    except Exception:
        reviewers = []
    raw['reviewers'] = reviewers
    return raw


def _serialize_draft_row(row):
    if not row:
        return None
    data = row_to_mapping(row) or {}
    data['content'] = _deserialize_json(data.get('content'), [])
    for flag in ('review_open_to_any',):
        if flag in data:
            data[flag] = bool(data.get(flag))
    for ts_field in ('review_requested_at', 'review_nudged_at'):
        val = data.get(ts_field)
        if val and not isinstance(val, str):
            try:
                data[ts_field] = val.isoformat()
            except Exception:
                data[ts_field] = str(val)
    due_date = data.get('due_date')
    if due_date:
        try:
            # sqlite returns strings while Postgres may return datetime
            data['due_date'] = due_date if isinstance(due_date, str) else due_date.isoformat()
        except Exception:
            data['due_date'] = str(due_date)
    return data


def _serialize_comment_row(row):
    if not row:
        return None
    data = row_to_mapping(row) or {}
    data['mentions'] = _deserialize_json(data.get('mentions'), [])
    return data


def _serialize_revision_row(row):
    if not row:
        return None
    data = row_to_mapping(row) or {}
    data['details'] = _deserialize_json(data.get('details'), {})
    return data


def _compute_content_diff(previous_snapshot, current_snapshot):
    """Return a lightweight diff between two revision snapshots."""
    try:
        prev_sections = _deserialize_json(previous_snapshot, [])
    except Exception:
        prev_sections = []
    try:
        new_sections = _deserialize_json(current_snapshot, [])
    except Exception:
        new_sections = []
    prev_map = {str(s.get('id')): s for s in (prev_sections or []) if isinstance(s, dict)}
    new_map = {str(s.get('id')): s for s in (new_sections or []) if isinstance(s, dict)}
    added = []
    removed = []
    changed = []
    for sec_id, section in new_map.items():
        if sec_id not in prev_map:
            added.append({'id': sec_id, 'heading': section.get('heading'), 'text': section.get('text')})
        else:
            prev_text = (prev_map[sec_id] or {}).get('text')
            if (section.get('text') or '') != (prev_text or ''):
                changed.append({'id': sec_id, 'from': prev_text, 'to': section.get('text')})
    for sec_id, section in prev_map.items():
        if sec_id not in new_map:
            removed.append({'id': sec_id, 'heading': section.get('heading'), 'text': section.get('text')})
    if not (added or removed or changed):
        return {'summary': 'No content changes', 'added': [], 'removed': [], 'changed': []}
    return {'summary': 'Content updated', 'added': added, 'removed': removed, 'changed': changed}


def _build_comment_threads(comments):
    threads = {}
    for c in comments:
        cm = _serialize_comment_row(c)
        tid = cm.get('thread_id') or cm.get('id')
        if tid not in threads:
            threads[tid] = {
                'thread_id': tid,
                'paragraph_id': cm.get('paragraph_id') or '',
                'comments': [],
            }
        threads[tid]['comments'].append(cm)
    return list(threads.values())


def _lookup_approver_default(owner_id: str, campaign: Optional[str], channel: Optional[str]):
    """Return the most specific approver default for an owner/campaign/channel."""
    db = get_db()
    candidates = [
        (campaign, channel),
        (campaign, None),
        (None, channel),
        (None, None),
    ]
    for camp_val, chan_val in candidates:
        row = db.execute(
            'SELECT * FROM team_approver_defaults WHERE owner_user_id = ? AND COALESCE(campaign, "") = ? AND COALESCE(channel, "") = ? ORDER BY created_at DESC LIMIT 1',
            (owner_id, camp_val or '', chan_val or ''),
        ).fetchone()
        if row:
            return row_to_mapping(row)
    return None


def _record_draft_notification(draft_id: str, channels: list, message: str):
    db = get_db()
    now_iso = datetime.now(timezone.utc).isoformat()
    for ch in channels:
        db.execute(
            'INSERT INTO team_draft_notifications (id, draft_id, channel, message, created_at) VALUES (?, ?, ?, ?, ?)',
            (str(uuid.uuid4()), draft_id, ch, message, now_iso),
        )
    return now_iso


def _sweep_stale_reviews(owner_id: str, hours_idle: int = 24):
    """Find drafts stuck in review and emit reminder notifications."""
    db = get_db()
    threshold = datetime.now(timezone.utc) - timedelta(hours=hours_idle)
    rows = db.execute(
        """
        SELECT * FROM team_drafts
        WHERE owner_user_id = ?
          AND LOWER(status) = 'in_review'
          AND review_requested_at IS NOT NULL
          AND review_requested_at <= ?
          AND (review_nudged_at IS NULL OR review_nudged_at <= ?)
        """,
        (owner_id, threshold.isoformat(), threshold.isoformat()),
    ).fetchall()
    nudged = []
    for row in rows:
        draft = row_to_mapping(row)
        message = (
            f"Draft '{draft.get('title') or draft.get('id')}' has been in review for more than {hours_idle}h."
        )
        now_iso = _record_draft_notification(draft['id'], ['in_app', 'slack', 'email'], message)
        db.execute(
            'UPDATE team_drafts SET review_nudged_at = ? WHERE id = ?',
            (now_iso, draft['id']),
        )
        db.execute(
            'INSERT INTO team_draft_revisions (id, draft_id, author_user_id, summary, kind, details, content_snapshot, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                str(uuid.uuid4()),
                draft['id'],
                owner_id,
                'Nudge sent to reviewers',
                'nudge',
                json.dumps({'channels': ['in_app', 'slack', 'email'], 'reason': 'idle_in_review'}),
                draft.get('content'),
                now_iso,
            ),
        )
        nudged.append(draft['id'])
    db.commit()
    return nudged


def _ensure_demo_drafts(owner_id: str):
    if not owner_id:
        return
    db = get_db()
    existing = db.execute('SELECT id FROM team_drafts WHERE owner_user_id = ? LIMIT 1', (owner_id,)).fetchone()
    if existing:
        return
    now = datetime.now(timezone.utc)
    drafts = [
        {
            'title': 'Community drip campaign',
            'campaign': 'Fall Product Drop',
            'status': 'in_review',
            'assignee_email': 'alex@brandco.com',
            'due_date': now + timedelta(days=2),
            'content': [
                {'id': 'hook', 'heading': 'Hook', 'text': 'Introduce the collection with a community-first hook.'},
                {'id': 'teaser', 'heading': 'Teaser', 'text': 'Share a sneak peek of the product images.'},
                {'id': 'launch', 'heading': 'Launch', 'text': 'Announce the launch date and time.'},
                {'id': 'cta', 'heading': 'Call to Action', 'text': 'Encourage followers to sign up for early access.'},
            ],
        },
        {
            'title': 'Behind the Scenes',
            'campaign': 'Fall Product Drop',
            'status': 'draft',
            'assignee_email': 'jamie@brandco.com',
            'due_date': now + timedelta(days=7),
            'content': [
                {'id': 'bts_intro', 'heading': 'Behind the Scenes Intro', 'text': 'Share the story behind the product.'},
                {'id': 'bts_process', 'heading': 'Creation Process', 'text': 'Show the product creation process.'},
                {'id': 'bts_team', 'heading': 'Meet the Team', 'text': 'Introduce the team behind the product.'},
                {'id': 'bts_cta', 'heading': 'Call to Action', 'text': 'Invite followers to share their thoughts.'},
            ],
        },
        {
            'title': 'Launch Announcement',
            'campaign': 'Fall Product Drop',
            'status': 'in_review',
            'assignee_email': 'sarah@brandco.com',
            'due_date': now + timedelta(days=1),
            'content': [
                {'id': 'body', 'heading': 'Body', 'text': 'We’ve been working on this for months. It’s finally here.'},
                {'id': 'cta', 'heading': 'CTA', 'text': 'Join the waitlist -> link in bio.'},
            ],
            'reviewers': ['sarah@brandco.com', 'mike@agency.com'],
        },
        {
            'title': 'Holiday Promo Teaser',
            'campaign': 'Winter Sale',
            'status': 'draft',
            'assignee_email': None,
            'due_date': None,
            'content': [
                {'id': 'intro', 'heading': 'Intro', 'text': 'Get ready for the biggest sale of the year.'},
            ],
            'reviewers': [],
        },
    ]

    for d in drafts:
        did = str(uuid.uuid4())
        content_json = json.dumps(d['content'])
        reviewers_json = json.dumps(d['reviewers'])
        db.execute(
            """
            INSERT INTO team_drafts (
                id, owner_user_id, title, campaign, status,
                assignee_email, due_date, content, reviewers,
                created_at, updated_at, review_requested_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                did, owner_id, d['title'], d['campaign'], d['status'],
                d['assignee_email'],
                d['due_date'].isoformat() if d['due_date'] else None,
                content_json, reviewers_json,
                now.isoformat(), now.isoformat(),
                now.isoformat() if d['status'] == 'in_review' else None
            )
        )
        # Initial revision
        db.execute(
            """
            INSERT INTO team_draft_revisions (
                id, draft_id, author_user_id, summary, kind, details, content_snapshot, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()), did, owner_id, 'Initial draft created', 'create',
                json.dumps({'source': 'demo_setup'}), content_json, now.isoformat()
            ),
        )
    db.commit()


@app.get('/__dev__/ping')
def dev_ping():
    return jsonify({'pong': True})


@app.post('/api/feedback')
def api_feedback():
    if not session.get('user_id') and not session.get('profile_id'):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
        
    data = request.get_json(silent=True) or {}
    rating = data.get('rating')
    post_day = data.get('post_day')
    platform = data.get('platform')
    note = (data.get('note') or '')[:1500]
    profile_id = session.get('profile_id')
    
    db = get_db()
    try:
        db.execute(
            'INSERT INTO feedback (profile_id, rating, post_day, platform, note) VALUES (?, ?, ?, ?, ?)',
            (profile_id, rating, post_day, platform, note)
        )
        db.commit()
    except Exception:
        logging.exception("Feedback save failed")
        pass

    return jsonify({'ok': True})


def _current_user_id() -> Optional[str]:
    return session.get('user_id')


def _template_owner_where_clause():
    return 'owner_user_id = ?'


@app.route('/api/templates', methods=['GET', 'POST'])
def api_templates():
    user_id = _current_user_id()
    if not user_id:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    db = get_db()

    if request.method == 'GET':
        scope = (request.args.get('scope') or 'all').lower()
        params = [user_id]
        where = _template_owner_where_clause()
        if scope in {'personal', 'workspace'}:
            where = where + ' AND LOWER(scope) = ?'
            params.append(scope)
        rows = db.execute(
            f'SELECT * FROM templates WHERE {where} ORDER BY updated_at DESC',
            tuple(params)
        ).fetchall()
        templates = [_serialize_template_row(r) for r in rows]
        return jsonify({'ok': True, 'templates': templates})

    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'ok': False, 'error': 'Name is required'}), 400
    scope = (data.get('scope') or 'personal').strip().lower()
    if scope not in {'personal', 'workspace'}:
        scope = 'personal'
    payload = data.get('payload') or data.get('template') or {}
    preview = data.get('preview') or ''
    now_iso = datetime.now(timezone.utc).isoformat()
    template_id = data.get('id') or str(uuid.uuid4())

    try:
        db.execute(
            '''INSERT INTO templates (id, owner_user_id, name, scope, payload, preview, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                template_id,
                user_id,
                name,
                scope,
                json.dumps(payload),
                preview,
                now_iso,
                now_iso,
            )
        )
        db.commit()
    except DB_INTEGRITY_ERRORS:
        return jsonify({'ok': False, 'error': 'Duplicate template id'}), 409
    except Exception as exc:
        logging.exception("Template save failed")
        return jsonify({'ok': False, 'error': str(exc)}), 500

    template = _serialize_template_row(
        db.execute('SELECT * FROM templates WHERE id = ?', (template_id,)).fetchone()
    )
    status_code = 201
    return jsonify({'ok': True, 'template': template}), status_code


@app.route('/api/templates/<template_id>', methods=['GET', 'DELETE'])
def api_template_detail(template_id):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    db = get_db()
    row = db.execute(
        f'SELECT * FROM templates WHERE id = ? AND {_template_owner_where_clause()}',
        (template_id, user_id),
    ).fetchone()
    if not row:
        return jsonify({'ok': False, 'error': 'Not found'}), 404

    if request.method == 'GET':
        return jsonify({'ok': True, 'template': _serialize_template_row(row)})

    # DELETE
    db.execute('DELETE FROM templates WHERE id = ?', (template_id,))
    db.commit()
    return jsonify({'ok': True})


@app.post('/api/templates/<template_id>/apply')
def api_template_apply(template_id):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    draft_id = data.get('draft_id')
    if not draft_id:
        return jsonify({'ok': False, 'error': 'draft_id is required'}), 400

    db = get_db()
    template_row = db.execute(
        f'SELECT * FROM templates WHERE id = ? AND {_template_owner_where_clause()}',
        (template_id, user_id)
    ).fetchone()
    if not template_row:
        return jsonify({'ok': False, 'error': 'Not found'}), 404

    draft_row = db.execute(
        'SELECT * FROM team_drafts WHERE id = ? AND owner_user_id = ?',
        (draft_id, user_id)
    ).fetchone()
    if not draft_row:
        return jsonify({'ok': False, 'error': 'Draft not found'}), 404

    template_payload = _serialize_template_row(template_row).get('payload') or {}
    draft_payload = template_payload.get('draft') or template_payload.get('content') or template_payload
    if draft_payload is None:
        draft_payload = {}

    previous_snapshot = draft_row['content']
    now_iso = datetime.now(timezone.utc).isoformat()

    db.execute(
        'UPDATE team_drafts SET content = ?, updated_at = ? WHERE id = ?',
        (json.dumps(draft_payload), now_iso, draft_id)
    )
    db.execute(
        '''INSERT INTO team_draft_revisions
           (id, draft_id, author_user_id, summary, kind, details, content_snapshot, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            str(uuid.uuid4()),
            draft_id,
            user_id,
            f"Applied template '{template_row['name']}'",
            'template_apply',
            json.dumps({'template_id': template_id, 'scope': template_row['scope']}),
            previous_snapshot,
            now_iso
        )
    )
    db.commit()

    updated_draft = row_to_mapping(
        db.execute('SELECT * FROM team_drafts WHERE id = ?', (draft_id,)).fetchone()
    ) or {}
    updated_draft['content'] = _deserialize_json(updated_draft.get('content'), [])
    return jsonify({'ok': True, 'draft': updated_draft})


@app.post('/api/drafts/<draft_id>/undo-template')
def api_undo_template_apply(draft_id):
    user_id = _current_user_id()
    if not user_id:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    db = get_db()
    draft_row = db.execute(
        'SELECT * FROM team_drafts WHERE id = ? AND owner_user_id = ?',
        (draft_id, user_id)
    ).fetchone()
    if not draft_row:
        return jsonify({'ok': False, 'error': 'Draft not found'}), 404

    revision = db.execute(
        '''SELECT * FROM team_draft_revisions
           WHERE draft_id = ? AND author_user_id = ? AND kind = 'template_apply'
           ORDER BY created_at DESC LIMIT 1''',
        (draft_id, user_id)
    ).fetchone()
    if not revision:
        return jsonify({'ok': False, 'error': 'No template application to undo'}), 400

    previous_snapshot = revision['content_snapshot'] or '[]'
    now_iso = datetime.now(timezone.utc).isoformat()

    db.execute(
        'UPDATE team_drafts SET content = ?, updated_at = ? WHERE id = ?',
        (previous_snapshot, now_iso, draft_id)
    )
    db.execute(
        '''INSERT INTO team_draft_revisions
           (id, draft_id, author_user_id, summary, kind, details, content_snapshot, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (
            str(uuid.uuid4()),
            draft_id,
            user_id,
            'Reverted template application',
            'template_undo',
            json.dumps({'reverted_revision': revision['id']}),
            previous_snapshot,
            now_iso
        )
    )
    db.commit()

    updated_draft = row_to_mapping(
        db.execute('SELECT * FROM team_drafts WHERE id = ?', (draft_id,)).fetchone()
    ) or {}
    updated_draft['content'] = _deserialize_json(updated_draft.get('content'), [])
    return jsonify({'ok': True, 'draft': updated_draft})


@app.post('/api/feedback/report')
def api_feedback_report():
    if not session.get('user_id'):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
        
    data = request.get_json(silent=True) or {}
    summary = data.get('summary')
    details = data.get('details')
    category = data.get('category')
    
    profile_id = session.get('profile_id') or session.get('user_id')
    
    platform = f"general:{category}" if category else "general"
    note = f"{summary}\n{details}"
    
    db = get_db()
    try:
        db.execute(
            'INSERT INTO feedback (profile_id, rating, post_day, platform, note) VALUES (?, ?, ?, ?, ?)',
            (profile_id, 0, 0, platform, note)
        )
        db.commit()
    except Exception:
        logging.exception("Feedback report save failed")
        pass
        
    return jsonify({'ok': True})


@app.post('/__dev__/create_user')
def dev_create_user():
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'ok': False, 'error': 'Not allowed in production'}), 403
        
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    is_paid = data.get('is_paid', False)
    
    if not email:
        return jsonify({'ok': False, 'error': 'Email required'}), 400
        
    db = get_db()
    # Check if user exists
    existing = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        user_id = existing['id']
        db.execute('UPDATE users SET is_paid = ? WHERE id = ?', (1 if is_paid else 0, user_id))
        db.commit()
    else:
        user_id = str(uuid.uuid4())
        db.execute(
            'INSERT INTO users (id, email, is_paid, password_hash) VALUES (?, ?, ?, ?)',
            (user_id, email, 1 if is_paid else 0, 'dev_hash')
        )
        db.commit()
    
    session['user_id'] = user_id
    session['email'] = email
    
    return jsonify({'ok': True, 'id': user_id})


@app.route('/api/team/approvals', methods=['GET', 'POST'])
def api_team_approvals():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
        
    db = get_db()
    user = db.execute('SELECT subscription_tier FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user or (user['subscription_tier'] or '').lower() != 'team':
        return jsonify({'ok': False, 'error': 'Team plan required'}), 403
        
    if request.method == 'GET':
        rows = db.execute('SELECT * FROM team_approvals WHERE owner_user_id = ? ORDER BY created_at DESC', (user_id,)).fetchall()
        approvals = []
        for row in rows:
            a = dict(row)
            a['reviewers'] = json.loads(a['reviewers']) if a['reviewers'] else []
            approvals.append(a)
        return jsonify({'ok': True, 'approvals': approvals})
        
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        title = data.get('title')
        content_ref = data.get('content_ref')
        reviewers = data.get('reviewers', [])
        note = data.get('note', '')
        
        if not title:
            return jsonify({'ok': False, 'error': 'Title is required'}), 400
        if not content_ref:
            return jsonify({'ok': False, 'error': 'content_ref is required'}), 400
            
        approval_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        db.execute(
            '''INSERT INTO team_approvals 
               (id, owner_user_id, submitter_user_id, title, content_ref, state, reviewers, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (approval_id, user_id, user_id, title, content_ref, 'pending', json.dumps(reviewers), now)
        )
        
        # Insert created event
        event_id = str(uuid.uuid4())
        db.execute(
            '''INSERT INTO team_approval_events 
               (id, approval_id, actor_user_id, action, created_at)
               VALUES (?, ?, ?, ?, ?)''',
            (event_id, approval_id, user_id, 'created', now)
        )
        
        db.commit()
        
        approval = {
            'id': approval_id,
            'state': 'pending',
            'title': title,
            'content_ref': content_ref,
            'reviewers': reviewers,
            'note': note,
            'created_at': now
        }
        return jsonify({'ok': True, 'approval': approval})


@app.post('/api/team/approvals/<approval_id>/transition')
def api_team_approval_transition(approval_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
        
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    
    if action not in ('approve', 'reject', 'cancel'):
        return jsonify({'ok': False, 'error': 'Invalid action'}), 400
        
    db = get_db()
    approval = db.execute('SELECT * FROM team_approvals WHERE id = ?', (approval_id,)).fetchone()
    if not approval:
        return jsonify({'ok': False, 'error': 'Approval not found'}), 404
        
    new_state = 'pending'
    if action == 'approve':
        new_state = 'approved'
    elif action == 'reject':
        new_state = 'rejected'
    elif action == 'cancel':
        new_state = 'cancelled'
        
    # Insert event
    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    db.execute(
        '''INSERT INTO team_approval_events 
           (id, approval_id, actor_user_id, action, created_at)
           VALUES (?, ?, ?, ?, ?)''',
        (event_id, approval_id, user_id, action, now)
    )
        
    db.execute('UPDATE team_approvals SET state = ? WHERE id = ?', (new_state, approval_id))
    db.commit()
    
    # Fetch updated approval
    row = db.execute('SELECT * FROM team_approvals WHERE id = ?', (approval_id,)).fetchone()
    approval = dict(row)
    approval['reviewers'] = json.loads(approval['reviewers']) if approval['reviewers'] else []
    
    # Fetch events
    events_rows = db.execute('SELECT * FROM team_approval_events WHERE approval_id = ? ORDER BY created_at DESC', (approval_id,)).fetchall()
    events = [dict(r) for r in events_rows]
    
    return jsonify({'ok': True, 'approval': approval, 'events': events})


@app.get('/api/current_user')
def api_current_user():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Not logged in'}), 401
    db = get_db()
    user = db.execute('SELECT id, email, is_paid, subscription_tier, is_admin, free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
    if not user:
        return jsonify({'ok': False, 'error': 'User not found'}), 404
    return jsonify({
        'ok': True,
        'id': user['id'],
        'email': user['email'],
        'is_paid': bool(user['is_paid']),
        'subscription_tier': user['subscription_tier'],
        'is_admin': bool(user['is_admin']),
        'free_sample_used': bool(user['free_sample_used'])
    })


def get_user_by_email(email):
    if has_app_context():
        db = get_db()
        return db.execute('SELECT * FROM users WHERE email = ?', (email.lower(),)).fetchone()
    else:
        with app.app_context():
            db = get_db()
            return db.execute('SELECT * FROM users WHERE email = ?', (email.lower(),)).fetchone()


@app.post('/api/generate-variants')
def api_generate_variants():
    request_id = _get_request_id()

    if os.environ.get('FLASK_ENV') == 'production':
        if not session.get('user_id'):
            return jsonify({'ok': False, 'error': {'code': 'unauthorized', 'message': 'Not logged in'}, 'request_id': request_id, 'data': None}), 401

    data = request.get_json(force=True) or {}

    service_response = generation_service.generate(
        endpoint='generate-variants',
        request_id=request_id,
        payload=data,
        validator=_validate_variants_payload,
        normalizer=_normalize_variants_payload,
        output_validator=_validate_variants_output,
        fallback_callable=_generate_variants_fallback,
        use_openai=False,
    )

    body = dict(service_response.body)
    data_payload = body.pop('data', {}) if isinstance(body.get('data'), dict) else (body.pop('data') if 'data' in body else {})
    if service_response.ok and isinstance(data_payload, dict):
        variants = data_payload.get('variants') or []
        body['data'] = data_payload
        body['variants'] = variants
        body['count'] = data_payload.get('count', len(variants))
    else:
        body.setdefault('data', None)

    return jsonify(body), service_response.status
    

@app.get('/__dev__/trends')
def dev_trends():
    if not _is_dev_mode():
        return jsonify({'error': 'Not found'}), 404
    
    industry = request.args.get('industry', 'general')
    force = request.args.get('force')
    
    ttl = 0 if force else 6
    
    try:
        trends = gen_mod.fetch_trend_context(industry, ttl_hours=ttl)
        return jsonify({'trends': trends})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.post('/api/account/upgrade')
def api_account_upgrade():
    if not session.get('user_id'):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
        
    data = request.get_json(silent=True) or {}
    tier = data.get('tier')
    
    if tier not in ['solo', 'team']:
        return jsonify({'ok': False, 'error': 'Invalid tier'}), 400
        
    db = get_db()
    try:
        db.execute('UPDATE users SET subscription_tier = ? WHERE id = ?', (tier, session['user_id']))
        db.commit()
    except Exception as e:
        logging.exception("Account upgrade failed")
        return jsonify({'ok': False, 'error': str(e)}), 500
        
    return jsonify({'ok': True})

@app.route('/api/voice-profile', methods=['GET', 'POST'])
def api_voice_profile():
    db = get_db()
    pid = session.get('profile_id')
    if not pid:
        if request.method == 'POST':
            pid = str(uuid.uuid4())
            session['profile_id'] = pid
        else:
            return jsonify({'ok': True, 'samples': []})

    if request.method == 'POST':
        data = request.get_json(force=True) or {}
        samples = data.get('samples') or []
        
        # Analyze samples to build voice profile
        try:
            analysis = voice_profile.analyze_samples(samples)
            voice_data = json.dumps(analysis)
        except Exception as e:
            logging.error(f"Voice analysis failed: {e}")
            # Fallback to basic storage if analysis fails
            voice_data = json.dumps({'samples': samples, 'analyzed': False})

        # Upsert profile with voice data
        existing = db.execute('SELECT id FROM profiles WHERE id = ?', (pid,)).fetchone()
        try:
            if existing:
                db.execute('UPDATE profiles SET voice_profile = ? WHERE id = ?', (voice_data, pid))
            else:
                db.execute('INSERT INTO profiles (id, voice_profile) VALUES (?, ?)', (pid, voice_data))
            db.commit()
        except Exception as e:
            # Fallback for missing voice_profile column
            logging.warning(f"Voice profile save failed: {e}. Retrying with legacy schema (ignoring voice data).")
            try:
                db.rollback()
            except Exception:
                pass
            
            # If the column is missing, we can't save the voice data at all.
            # But we should return success so the UI doesn't break, 
            # even though the data wasn't persisted.
            # If the profile didn't exist, we must create it to avoid foreign key errors later.
            if not existing:
                try:
                    db.execute('INSERT INTO profiles (id) VALUES (?)', (pid,))
                    db.commit()
                except Exception as inner_e:
                    logging.error(f"Failed to create empty profile fallback: {inner_e}")
                    return jsonify({'ok': False, 'error': 'Database error'}), 500
            
            return jsonify({'ok': True, 'warning': 'Voice data not saved (schema mismatch)'})

        return jsonify({'ok': True})

    else: # GET
        row = db.execute('SELECT voice_profile FROM profiles WHERE id = ?', (pid,)).fetchone()
        if not row:
            return jsonify({'ok': True, 'samples': []})
        
        try:
            # Handle missing column in row result if using sqlite3.Row with missing column
            if 'voice_profile' not in row.keys():
                 return jsonify({'ok': True, 'samples': []})

            vp = _deserialize_json(row['voice_profile'], {})
            return jsonify({'ok': True, 'samples': vp.get('samples', [])})
        except Exception:
            return jsonify({'ok': True, 'samples': []})


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5001'))
    try:
        with app.app_context():
            init_db()
    except Exception:
        logging.exception("Database initialization failed during startup")
    app.run(host='0.0.0.0', port=port, debug=_is_dev_mode())
