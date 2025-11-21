import os, sqlite3, uuid, json, re
from datetime import date
from datetime import datetime, timezone
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, g, session, redirect, has_app_context, url_for
import logging
import threading
import time
import math
from flask_cors import CORS
import generator as gen_mod
from werkzeug.security import generate_password_hash, check_password_hash
from typing import TYPE_CHECKING, Any, Optional, Tuple
import requests
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
try:
    if TYPE_CHECKING:
        # ensure type-checkers know about stripe without requiring it at runtime
        import stripe  # type: ignore
    else:
        import stripe
except Exception:
    stripe = None

IMAGE_DATA_URL_MAX_BYTES = 2_500_000  # ~2.5MB encoded payload cap for inline uploads
MAX_FEEDBACK_NOTE_LEN = 1500
try:
    TEAM_MEMBER_LIMIT = int(os.getenv('TEAM_MEMBER_LIMIT', '10'))
except (TypeError, ValueError):
    TEAM_MEMBER_LIMIT = 10

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
    format="%(asctime)s %(levelname)s [req=%(request_id)s] %(message)s",
)


class RequestIdMissingFilter(logging.Filter):
    """Ensure log records always have request_id to satisfy the formatter."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, 'request_id'):
            record.request_id = 'n/a'
        return True


logging.getLogger().addFilter(RequestIdMissingFilter())
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
# 2) repo-local `swelly.db` (new default)
# 3) repo-local `togetherly.db` (legacy fallback during transition)
_default_db = os.path.join(os.path.dirname(__file__), "swelly.db")
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
        DB_INTEGRITY_ERRORS = DB_INTEGRITY_ERRORS + (_pg_errors.UniqueViolation, _pg_errors.ForeignKeyViolation)
    except Exception:
        pass

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


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = getattr(g, 'request_id', 'n/a')
        return True


app.logger.addFilter(RequestIdFilter())


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
        prompt = {
            'instruction': 'Create social media posts as structured JSON.',
            'requirements': payload
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
        instructions = [
            "Look at the attached inspiration image and craft polished social posts that reference what you see.",
            "Blend the visual cues with the requirements JSON below.",
            "Respond with ONLY a JSON array of post objects (same schema as other generation responses).",
        ]
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

    def close(self):
        return self._conn.close()


def _connect_db():
    """Return a DB connection using Postgres if configured, otherwise sqlite."""
    if USE_POSTGRES:
        if not psycopg:
            raise RuntimeError("psycopg is required for Postgres connections; install dependencies.")
        conn = psycopg.connect(DATABASE_URL, autocommit=False)
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
    db.commit()

    # Dev-only: seed a known admin user for local development to simplify testing
    try:
        if os.getenv('FLASK_ENV') == 'development' or os.getenv('ALLOW_DEV_DEBUG') == '1':
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

@app.before_request
def ensure_db():
    init_db()

def _db_healthcheck():
    try:
        db = get_db()
        db.execute('SELECT 1')
        return True, None
    except Exception as exc:
        return False, str(exc)


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
    checks = {}
    checks['database'] = 'connected' if healthy else f"unhealthy: {db_error or 'unknown'}"
    checks['stripe'] = 'configured' if (os.getenv('STRIPE_SECRET_KEY') and stripe) else 'not_configured'
    checks['openai'] = 'configured' if USE_OPENAI else 'not_configured'
    checks['github_feedback'] = 'configured' if GITHUB_FEEDBACK_TOKEN else 'not_configured'

    status = 'healthy' if healthy else 'unhealthy'
    status_code = 200 if healthy else 503
    payload = {
        'status': status,
        'version': os.getenv('APP_VERSION', 'dev'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': checks
    }
    return jsonify(payload), status_code


@app.get("/health")
def legacy_health():
    """Back-compat endpoint; proxies to /readyz."""
    return readyz()

def _initial_user_payload():
    uid = session.get('user_id')
    if not uid:
        return None
    try:
        db = get_db()
        row = db.execute('SELECT id, email, is_paid, free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
    except Exception:
        return None
    if not row:
        return None
    return {
        'id': row['id'],
        'email': row['email'],
        'is_paid': bool(row['is_paid']),
        'free_sample_used': bool(row['free_sample_used']) if row['free_sample_used'] is not None else False
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
    is_dev = os.getenv('FLASK_ENV') == 'development' or os.getenv('ALLOW_DEV_DEBUG') == '1'
    return render_template("index.html", is_dev=is_dev, initial_user=_initial_user_payload())


@app.get("/generate")
def generate_page():
    """Dashboard for generating content after onboarding completes."""
    is_dev = os.getenv('FLASK_ENV') == 'development' or os.getenv('ALLOW_DEV_DEBUG') == '1'
    return render_template("dashboard.html", is_dev=is_dev, initial_user=_initial_user_payload())


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
    """Page for generating responses to customer reviews."""
    return render_template("review_response.html")


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
    except sqlite3.IntegrityError:
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
    user = db.execute('SELECT id, is_paid, stripe_customer_id FROM users WHERE id = ?', (uid,)).fetchone()
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
    return render_template('account.html', user=user, subscription=subscription, is_admin=admin_flag, admin_csrf=admin_csrf)


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
    except sqlite3.IntegrityError:
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


def _current_team_user():
    user_row = _get_current_user_row()
    if not user_row:
        return None
    mapped = row_to_mapping(user_row)
    tier = (mapped.get('subscription_tier') or '').lower()
    if tier == 'team' or mapped.get('is_admin'):
        return mapped
    return None


@app.get('/api/team/approvals')
def api_team_approvals_list():
    user_row = _current_team_user()
    if not user_row:
        return jsonify({'ok': False, 'error': 'Team plan required'}), 403
    owner_id = user_row['id']
    db = get_db()
    rows = db.execute('SELECT * FROM team_approvals WHERE owner_user_id = ? ORDER BY created_at DESC', (owner_id,)).fetchall()
    return jsonify({'ok': True, 'approvals': [ _serialize_approval_row(r) for r in rows ]})


@app.post('/api/team/approvals')
def api_team_approvals_create():
    rl = _enforce_rate_limit(f"{request.remote_addr}:team-approvals-create", capacity=15, refill_seconds=300)
    if rl:
        return rl
    user_row = _current_team_user()
    if not user_row:
        return jsonify({'ok': False, 'error': 'Team plan required'}), 403
    data = request.get_json(force=True) or {}
    title = (data.get('title') or '').strip()
    content_ref = (data.get('content_ref') or '').strip()
    reviewers = data.get('reviewers') or []
    if not title:
        return jsonify({'ok': False, 'error': 'Title is required'}), 400
    if not content_ref:
        return jsonify({'ok': False, 'error': 'content_ref is required'}), 400
    if not isinstance(reviewers, list):
        reviewers = []
    reviewers = [str(x).strip() for x in reviewers if str(x).strip()]
    aid = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    db = get_db()
    db.execute(
        'INSERT INTO team_approvals (id, owner_user_id, submitter_user_id, title, content_ref, state, reviewers, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
        (aid, user_row['id'], user_row['id'], title, content_ref, 'pending', json.dumps(reviewers), now_iso, now_iso)
    )
    db.execute(
        'INSERT INTO team_approval_events (id, approval_id, actor_user_id, action, note, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (str(uuid.uuid4()), aid, user_row['id'], 'created', data.get('note'), now_iso)
    )
    db.commit()
    row = db.execute('SELECT * FROM team_approvals WHERE id = ?', (aid,)).fetchone()
    return jsonify({'ok': True, 'approval': _serialize_approval_row(row)})


@app.post('/api/team/approvals/<approval_id>/transition')
def api_team_approvals_transition(approval_id: str):
    rl = _enforce_rate_limit(f"{request.remote_addr}:team-approvals-transition", capacity=30, refill_seconds=300)
    if rl:
        return rl
    user_row = _current_team_user()
    if not user_row:
        return jsonify({'ok': False, 'error': 'Team plan required'}), 403
    data = request.get_json(force=True) or {}
    action = (data.get('action') or '').strip().lower()
    if action not in ('approve', 'changes_requested'):
        return jsonify({'ok': False, 'error': 'Action must be approve or changes_requested'}), 400
    db = get_db()
    row = db.execute('SELECT * FROM team_approvals WHERE id = ?', (approval_id,)).fetchone()
    if not row:
        return jsonify({'ok': False, 'error': 'Approval not found'}), 404
    if row['owner_user_id'] != user_row['id'] and row['submitter_user_id'] != user_row['id'] and not user_row.get('is_admin'):
        return jsonify({'ok': False, 'error': 'Not authorized'}), 403
    new_state = 'approved' if action == 'approve' else 'changes_requested'
    now_iso = datetime.now(timezone.utc).isoformat()
    db.execute('UPDATE team_approvals SET state = ?, updated_at = ? WHERE id = ?', (new_state, now_iso, approval_id))
    db.execute(
        'INSERT INTO team_approval_events (id, approval_id, actor_user_id, action, note, created_at) VALUES (?, ?, ?, ?, ?, ?)',
        (str(uuid.uuid4()), approval_id, user_row['id'], action, data.get('note'), now_iso)
    )
    db.commit()
    updated = db.execute('SELECT * FROM team_approvals WHERE id = ?', (approval_id,)).fetchone()
    events = db.execute('SELECT * FROM team_approval_events WHERE approval_id = ? ORDER BY created_at DESC', (approval_id,)).fetchall()
    return jsonify({'ok': True, 'approval': _serialize_approval_row(updated), 'events': [dict(e) for e in events]})


### DB helpers
def get_user_by_email(email: str):
    # Helper used in tests; prefer using the app context DB when available.
    # If not in an application context, open a direct sqlite connection to DB_PATH
    try:
        if has_app_context():
            db = get_db()
            return db.execute('SELECT * FROM users WHERE email = ?', (email.lower(),)).fetchone()
    except Exception:
        # fall through to file-based DB lookup
        pass
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.execute('SELECT * FROM users WHERE email = ?', (email.lower(),))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        return None

def get_user_by_id(uid: str):
    try:
        if has_app_context():
            db = get_db()
            return db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    except Exception:
        pass
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.execute('SELECT * FROM users WHERE id = ?', (uid,))
        row = cur.fetchone()
        conn.close()
        return row
    except Exception:
        return None


def row_to_mapping(x):
    """Convert sqlite3.Row or list-of-rows to plain Python dict(s).

    - If x is None, return None.
    - If x is a sqlite3.Row, return dict(x).
    - If x is a list/tuple of sqlite3.Row, return a list of dicts.
    - If x is already a dict, return it unchanged.
    """
    if x is None:
        return None
    # sqlite3.Row doesn't implement isinstance check to a dedicated class
    try:
        if isinstance(x, sqlite3.Row):
            return dict(x)
    except Exception:
        # some sqlite3 versions may not support direct isinstance checks; fallback below
        pass
    # list/tuple of rows
    if isinstance(x, (list, tuple)):
        out = []
        for it in x:
            try:
                if isinstance(it, sqlite3.Row):
                    out.append(dict(it))
                else:
                    out.append(it)
            except Exception:
                out.append(it)
        return out
    # dict-like passthrough
    if isinstance(x, dict):
        return x
    return x

def set_user_paid(uid: str, paid: bool = True):
    db = get_db()
    try:
        db.execute('UPDATE users SET is_paid = ? WHERE id = ?', (1 if paid else 0, uid))
        db.commit()
    except Exception:
        pass


def _ensure_profile_id() -> str:
    """Return the profile identifier tied to the current user/session."""
    uid = session.get('user_id')
    if uid:
        session['profile_id'] = uid
        return uid
    pid = session.get('profile_id')
    if not pid:
        pid = str(uuid.uuid4())
        session['profile_id'] = pid
    return pid


def _normalize_company(name: str) -> str:
    if not name:
        return ""
    words = [w for w in re.split(r"\s+", name.strip()) if w]
    return " ".join([(w[0].upper() + w[1:]) if w else '' for w in words])


def _validate_company(name: str):
    if not name:
        return None
    if len(name) > 100:
        return 'Company name is too long (max 100 chars).'
    if re.search(r"[\x00-\x1F]", name):
        return 'Company name contains invalid characters.'
    if re.search(r"[<>*\\]", name):
        return 'Company name contains invalid characters.'
    if not re.match(r"^[\w \-'.&]+$", name):
        return 'Company name contains invalid characters.'
    return None


def _deserialize_json(value, default):
    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except Exception:
        return default


def _profile_row_to_dict(row):
    if not row:
        return {}
    return {
        'id': row['id'],
        'industry': row['industry'] or '',
        'tone': row['tone'] or '',
        'platforms': _deserialize_json(row['platforms'], []),
        'brand_keywords': _deserialize_json(row['brand_keywords'], []),
        'niche_keywords': _deserialize_json(row['niche_keywords'], []),
        'goals': _deserialize_json(row['goals'], []),
        'company': row['company'] or '',
        'include_images': bool(row['include_images']) if row['include_images'] is not None else True,
        'details': _deserialize_json(row['details'], {})
    }


def _get_active_profile_dict():
    """Return the current profile (if any) as a plain dict."""
    pid = session.get('user_id') or session.get('profile_id')
    if not pid:
        return None
    db = get_db()
    row = db.execute('SELECT * FROM profiles WHERE id = ?', (pid,)).fetchone()
    if not row:
        return None
    return _profile_row_to_dict(row)


def _is_dev_mode() -> bool:
    return os.getenv('FLASK_ENV') == 'development' or os.getenv('ALLOW_DEV_DEBUG') == '1'


def _get_current_user_row():
    uid = session.get('user_id')
    if not uid:
        return None
    db = get_db()
    return db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()


def _serialize_user_row(row):
    if not row:
        return None
    return {
        'id': row['id'],
        'email': row['email'],
        'is_paid': bool(row['is_paid']),
        'free_sample_used': bool(row['free_sample_used']) if row['free_sample_used'] is not None else False
    }


def _get_user_email(row) -> Optional[str]:
    if not row:
        return None
    if isinstance(row, dict):
        return row.get('email')
    try:
        return row['email']
    except (TypeError, KeyError):
        return getattr(row, 'email', None)


def _mark_free_sample_used(uid: str):
    if not uid:
        return
    db = get_db()
    db.execute('UPDATE users SET free_sample_used = 1 WHERE id = ?', (uid,))
    db.commit()


def _short_video_requested(platforms):
    targets = {'short_video', 'reels', 'reel', 'short-form', 'vertical_video'}
    for item in platforms or []:
        if not isinstance(item, str):
            continue
        if item.strip().lower() in targets:
            return True
    return False


def _current_usage_period() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m')


def _check_reels_quota(user_id: Optional[str], amount: int) -> Tuple[bool, Optional[int]]:
    if not user_id or amount <= 0:
        return True, None
    try:
        quota = int(os.getenv('REELS_QUOTA_MONTHLY', '30') or 0)
    except Exception:
        quota = 0
    if quota <= 0:
        return True, None
    db = get_db()
    period = _current_usage_period()
    row = db.execute('SELECT reels_generated FROM generation_usage WHERE user_id = ? AND period = ?', (user_id, period)).fetchone()
    used = row['reels_generated'] if row else 0
    if (used or 0) + amount > quota:
        return False, max(0, quota - (used or 0))
    return True, quota - ((used or 0) + amount)


def _increment_reels_usage(user_id: Optional[str], amount: int):
    if not user_id or amount <= 0:
        return
    db = get_db()
    period = _current_usage_period()
    row = db.execute('SELECT id, reels_generated FROM generation_usage WHERE user_id = ? AND period = ?', (user_id, period)).fetchone()
    if row:
        db.execute('UPDATE generation_usage SET reels_generated = ? WHERE id = ?', ((row['reels_generated'] or 0) + amount, row['id']))
    else:
        db.execute('INSERT INTO generation_usage (id, user_id, period, reels_generated) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), user_id, period, amount))
    db.commit()


def _trim_feedback_text(value: Optional[str], limit: int = 4000) -> str:
    if not value:
        return ''
    text = str(value).strip()
    if len(text) > limit:
        return text[:limit]
    return text


def _build_feedback_issue_payload(issue_type: str, context: dict):
    ctx = context or {}
    profile = ctx.get('profile') if isinstance(ctx.get('profile'), dict) else {}
    user_email = ctx.get('user_email') or 'unknown@swelly.app'
    summary = _trim_feedback_text(ctx.get('summary') or ctx.get('note') or 'New feedback', 80) or 'New feedback'
    details = _trim_feedback_text(ctx.get('details') or ctx.get('note') or '')
    tone = ctx.get('tone') or (profile.get('tone') if isinstance(profile, dict) else '')
    industry = ctx.get('industry') or (profile.get('industry') if isinstance(profile, dict) else '')
    company = profile.get('company') if isinstance(profile, dict) else ''
    platforms = ctx.get('platforms') or (profile.get('platforms') if isinstance(profile, dict) else [])
    if isinstance(platforms, (list, tuple)):
        platforms = ', '.join([str(p) for p in platforms if p])

    base_context = []
    if industry:
        base_context.append(f"- **Industry:** {industry}")
    if tone:
        base_context.append(f"- **Tone:** {tone}")
    if company:
        base_context.append(f"- **Company:** {company}")
    if platforms:
        base_context.append(f"- **Platforms:** {platforms}")

    if issue_type == 'thumbs_down':
        platform = ctx.get('platform') or 'Unknown platform'
        post_day = ctx.get('post_day')
        note_block = details or '_User did not leave additional feedback._'
        post_snapshot = _trim_feedback_text(ctx.get('post_snapshot') or '', 1600) or '_No caption snapshot captured._'
        base_context.append(f"- **Platform:** {platform}")
        if post_day:
            base_context.append(f"- **Day index:** {post_day}")
        source = ctx.get('source') or 'dashboard'
        base_context.append(f"- **Source:** {source}")
        if ctx.get('plan_length'):
            base_context.append(f"- **Plan length:** {ctx.get('plan_length')} days")
        title = f"[Thumbs Down] {platform} day {post_day or '?'} — {summary}"
        body = f"""## Reporter note\n\n{note_block}\n\n## Generated content snapshot\n\n```\n{post_snapshot}\n```\n\n## Context\n\n{os.linesep.join(base_context) if base_context else 'No additional metadata supplied.'}\n\n---\n*Submitted by: {user_email}*\n*Auto-created from Generate dashboard thumbs-down*"""
        return title, body, ['thumbs-down']

    # default/general feedback
    category = (ctx.get('category') or 'idea').strip().lower()
    allow_contact = bool(ctx.get('allow_contact'))
    base_context.append(f"- **Category:** {category}")
    if ctx.get('platform'):
        base_context.append(f"- **Platform focus:** {ctx.get('platform')}")
    if ctx.get('plan_length'):
        base_context.append(f"- **Plan length:** {ctx.get('plan_length')} days")
    if ctx.get('source'):
        base_context.append(f"- **Source:** {ctx.get('source')}")
    base_context.append(f"- **OK to contact:** {'Yes' if allow_contact else 'No'}")
    metadata_block = os.linesep.join(base_context) if base_context else 'No additional metadata supplied.'
    safe_details = details or '_No extra details provided._'
    body = f"""## Summary\n\n{summary}\n\n## Details\n\n{safe_details}\n\n## Context\n\n{metadata_block}\n\n---\n*Submitted by: {user_email}*\n*Auto-created from Settings feedback form*"""
    title = f"[Feedback] {summary}"
    return title, body, ['settings-feedback', f'feedback-{category}']


def _maybe_create_feedback_issue(issue_type: str, context: dict):
    if not GITHUB_FEEDBACK_TOKEN or not GITHUB_FEEDBACK_REPO:
        return None
    if OUTBOUND_KILL_SWITCH:
        app.logger.info('Skipping GitHub feedback issue creation (outbound disabled)', extra={'service': 'github'})
        return None
    try:
        title, body, extra_labels = _build_feedback_issue_payload(issue_type, context)
    except Exception:
        app.logger.exception('Failed to build feedback issue payload')
        return None
    if not title or not body:
        return None
    payload: dict[str, Any] = {'title': title[:250], 'body': body}
    labels = list(FEEDBACK_AUTOMATION_CONFIG.get('labels') or [])
    for label in extra_labels or []:
        if label and label not in labels:
            labels.append(label)
    if labels:
        payload['labels'] = labels
    assignee = FEEDBACK_AUTOMATION_CONFIG.get('default_assignee')
    if assignee:
        payload['assignees'] = [assignee]
    owner_repo = GITHUB_FEEDBACK_REPO.split('/', 1)
    if len(owner_repo) != 2:
        app.logger.warning('Invalid GITHUB_FEEDBACK_REPO format: %s', GITHUB_FEEDBACK_REPO)
        return None
    owner, repo_name = owner_repo
    url = f'https://api.github.com/repos/{owner}/{repo_name}/issues'
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {GITHUB_FEEDBACK_TOKEN}',
        'X-GitHub-Api-Version': '2022-11-28'
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=GITHUB_FEEDBACK_TIMEOUT)
        if resp.ok:
            return resp.json()
        app.logger.warning('GitHub issue creation failed: %s', resp.text)
    except Exception:
        app.logger.exception('GitHub issue creation request failed')
    return None


def _coerce_str_list(value, default=None):
    if isinstance(value, (list, tuple, set)):
        items = [str(v).strip() for v in value if isinstance(v, str) and v.strip()]
        if items:
            return items
    elif isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(default, (list, tuple, set)):
        return [str(v).strip() for v in default if isinstance(v, str) and str(v).strip()]
    return list(default or []) if default else []


def _parse_start_day(value):
    if not value:
        return date.today()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except Exception:
            return date.today()
    return date.today()


def _merge_generation_payload(payload: dict, profile: Optional[dict]) -> dict:
    profile = dict(profile or {})
    payload = dict(payload or {})

    days_src = payload.get('days') or profile.get('plan_days') or profile.get('days') or 7
    try:
        days = int(days_src)
    except Exception:
        days = 7
    days = max(1, min(days, 30))

    platforms = _coerce_str_list(payload.get('platforms'), profile.get('platforms') or [])
    if not platforms and payload.get('platform'):
        platforms = _coerce_str_list([payload.get('platform')])
    if not platforms:
        platforms = ['instagram']

    base_details = profile.get('details') if isinstance(profile.get('details'), dict) else {}
    override_details = payload.get('details') if isinstance(payload.get('details'), dict) else {}
    details = dict(base_details) if isinstance(base_details, dict) else {}
    if isinstance(override_details, dict):
        details.update(override_details)

    include_images = payload.get('include_images')
    if include_images is None:
        include_images = profile.get('include_images', True)

    company = payload.get('company') or profile.get('company') or ''

    merged = {
        'days': days,
        'start_day': _parse_start_day(payload.get('start_day') or profile.get('start_day')),
        'industry': (payload.get('industry') or profile.get('industry') or 'Business').strip() or 'Business',
        'tone': (payload.get('tone') or profile.get('tone') or 'friendly').strip() or 'friendly',
        'platforms': platforms,
        'brand_keywords': _coerce_str_list(payload.get('brand_keywords'), profile.get('brand_keywords') or []),
        'niche_keywords': _coerce_str_list(payload.get('niche_keywords'), profile.get('niche_keywords') or []),
        'goals': _coerce_str_list(payload.get('goals'), profile.get('goals') or []),
        'include_images': bool(include_images),
        'details': details,
        'company': _normalize_company(company),
    }
    image_context = (payload.get('image_context') or '').strip()
    if image_context:
        merged['image_context'] = image_context[:500]
    return merged


@app.get('/api/profile')
def api_get_profile():
    pid = _ensure_profile_id()
    db = get_db()
    row = db.execute('SELECT * FROM profiles WHERE id = ?', (pid,)).fetchone()
    if not row:
        return jsonify({'id': pid})
    return jsonify(_profile_row_to_dict(row))


@app.post('/api/profile')
def api_save_profile():
    pid = _ensure_profile_id()
    payload = request.get_json(force=True) or {}

    company_raw = (payload.get('company') or '').strip()
    company_error = _validate_company(company_raw)
    if company_error:
        return jsonify({'ok': False, 'error': company_error, 'errors': {'company': company_error}}), 400
    company = _normalize_company(company_raw)

    def _clean_list(key):
        value = payload.get(key) or []
        if not isinstance(value, (list, tuple)):
            return []
        cleaned = []
        for item in value:
            if not isinstance(item, str):
                continue
            item = item.strip()
            if item:
                cleaned.append(item)
        # preserve order, drop duplicates
        seen = set()
        deduped = []
        for item in cleaned:
            if item.lower() in seen:
                continue
            seen.add(item.lower())
            deduped.append(item)
        return deduped

    include_images = bool(payload.get('include_images', True))
    raw_details = payload.get('details')
    details: dict[str, object]
    if isinstance(raw_details, dict):
        details = dict(raw_details)
    else:
        details = {}
    content_version = request.args.get('content_version') or ''
    if content_version:
        details.setdefault('_content_version', content_version)

    db = get_db()
    db.execute(
        '''INSERT INTO profiles (id, industry, tone, platforms, brand_keywords, niche_keywords, goals, company, include_images, details)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
             industry=excluded.industry,
             tone=excluded.tone,
             platforms=excluded.platforms,
             brand_keywords=excluded.brand_keywords,
             niche_keywords=excluded.niche_keywords,
             goals=excluded.goals,
             company=excluded.company,
             include_images=excluded.include_images,
             details=excluded.details''',
        (
            pid,
            (payload.get('industry') or '').strip(),
            (payload.get('tone') or '').strip(),
            json.dumps(_clean_list('platforms')),
            json.dumps(_clean_list('brand_keywords')),
            json.dumps(_clean_list('niche_keywords')),
            json.dumps(_clean_list('goals')),
            company,
            1 if include_images else 0,
            json.dumps(details)
        )
    )
    db.commit()

    row = db.execute('SELECT * FROM profiles WHERE id = ?', (pid,)).fetchone()
    return jsonify({'ok': True, 'id': pid, 'profile': _profile_row_to_dict(row)})


@app.get('/api/current_user')
def api_current_user():
    row = _get_current_user_row()
    if not row:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
    data = _serialize_user_row(row) or {}
    data['ok'] = True
    return jsonify(data)


@app.post('/api/login')
def api_login():
    rl = _enforce_rate_limit(f"{request.remote_addr}:login", capacity=20, refill_seconds=300)
    if rl:
        return rl
    data = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not password:
        return jsonify({'ok': False, 'error': 'Email and password required'}), 400
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if not row or not row['password_hash'] or not check_password_hash(row['password_hash'], password):
        return jsonify({'ok': False, 'error': 'Invalid credentials'}), 401
    session['user_id'] = row['id']
    session['profile_id'] = row['id']
    data = _serialize_user_row(row) or {}
    data['ok'] = True
    return jsonify(data)


@app.post('/api/logout')
def api_logout():
    session.pop('user_id', None)
    session.pop('profile_id', None)
    return jsonify({'ok': True})


@app.post('/api/request-password-reset')
def api_request_password_reset():
    data = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()
    if not email:
        return jsonify({'ok': False, 'error': 'Email required'}), 400
    db = get_db()
    row = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if not row:
        # Return success to avoid leaking which emails exist
        return jsonify({'ok': True})
    token = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    db.execute('INSERT OR REPLACE INTO password_reset_tokens (token, user_id, expires_at) VALUES (?, ?, ?)', (token, row['id'], expires_at.isoformat()))
    db.commit()
    # In lieu of email delivery, return token for dev/testing convenience
    return jsonify({'ok': True, 'token': token})


@app.post('/api/confirm-password-reset')
def api_confirm_password_reset():
    data = request.get_json(force=True) or {}
    token = (data.get('token') or '').strip()
    password = data.get('password') or ''
    if not token or not password or len(password) < 6:
        return jsonify({'ok': False, 'error': 'Valid token and password are required'}), 400
    db = get_db()
    row = db.execute('SELECT user_id, expires_at FROM password_reset_tokens WHERE token = ?', (token,)).fetchone()
    if not row:
        return jsonify({'ok': False, 'error': 'Invalid or expired token'}), 400
    expires_at = row['expires_at']
    if expires_at and isinstance(expires_at, str):
        try:
            if datetime.fromisoformat(expires_at) < datetime.now(timezone.utc):
                db.execute('DELETE FROM password_reset_tokens WHERE token = ?', (token,))
                db.commit()
                return jsonify({'ok': False, 'error': 'Token expired'}), 400
        except Exception:
            pass
    pw_hash = _hash_password(password)
    db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (pw_hash, row['user_id']))
    db.execute('DELETE FROM password_reset_tokens WHERE token = ?', (token,))
    db.commit()
    return jsonify({'ok': True})


@app.get('/__dev__/ping')
def dev_ping():
    """Simple health endpoint used by tests and helper scripts."""
    return ('pong', 200)


DEV_USER_TEMPLATES = {
    'free': {
        'label': 'Free (unpaid)',
        'is_paid': False,
        'is_admin': False,
        'subscription_tier': 'free',
        'stripe_customer_id': None,
    },
    'paid_solo': {
        'label': 'Paid – Solo',
        'is_paid': True,
        'is_admin': False,
        'subscription_tier': 'solo',
        'stripe_customer_id': 'dev-solo',
    },
    'paid_team_admin': {
        'label': 'Paid – Team admin',
        'is_paid': True,
        'is_admin': True,
        'subscription_tier': 'team',
        'stripe_customer_id': 'dev-team-shared',
    },
    'paid_team_member': {
        'label': 'Paid – Team member',
        'is_paid': True,
        'is_admin': False,
        'subscription_tier': 'team',
        'stripe_customer_id': 'dev-team-shared',
    },
}


@app.post('/__dev__/create_user')
def dev_create_user():
    if not _is_dev_mode():
        return jsonify({'ok': False, 'error': 'Not available'}), 404
    data = request.get_json(force=True) or {}
    base_email = (data.get('email') or f'dev-{uuid.uuid4().hex[:5]}@example.com').strip().lower()
    password = data.get('password') or 'password'
    requested_templates = data.get('templates')
    if isinstance(requested_templates, str):
        requested_templates = [requested_templates]
    templates = [t for t in (requested_templates or []) if t in DEV_USER_TEMPLATES]
    if not templates:
        template_key = data.get('template')
        if template_key and template_key in DEV_USER_TEMPLATES:
            templates = [template_key]
        elif 'is_paid' in data:
            templates = ['paid_solo' if data.get('is_paid') else 'free']
        else:
            templates = ['free']

    def alias_email(original: str, template_key: str, index: int) -> str:
        if index == 0:
            return original
        slug = template_key.replace('paid_', '').replace('_', '-') or f'user-{index}'
        if '@' not in original:
            return f'{slug}-{original}'
        local, domain = original.split('@', 1)
        return f"{local}+{slug}@{domain}"

    def upsert_dev_user(db_conn, email_value: str, template_key: str):
        template = DEV_USER_TEMPLATES.get(template_key, DEV_USER_TEMPLATES['free'])
        hashed = _hash_password(password)
        row = db_conn.execute('SELECT id FROM users WHERE email = ?', (email_value,)).fetchone()
        is_paid_val = 1 if template.get('is_paid') else 0
        is_admin_val = 1 if template.get('is_admin') else 0
        stripe_id = template.get('stripe_customer_id')
        sub_tier = template.get('subscription_tier')
        if row:
            uid_val = row['id']
            db_conn.execute('UPDATE users SET password_hash = ?, is_paid = ?, is_admin = ?, subscription_tier = ?, stripe_customer_id = ?, free_sample_used = 0 WHERE id = ?', (hashed, is_paid_val, is_admin_val, sub_tier, stripe_id, uid_val))
        else:
            uid_val = str(uuid.uuid4())
            db_conn.execute('INSERT INTO users (id, email, password_hash, is_paid, free_sample_used, is_admin, subscription_tier, stripe_customer_id) VALUES (?, ?, ?, ?, 0, ?, ?, ?)', (uid_val, email_value, hashed, is_paid_val, is_admin_val, sub_tier, stripe_id))
        return {
            'id': uid_val,
            'email': email_value,
            'is_paid': bool(is_paid_val),
            'is_admin': bool(is_admin_val),
            'subscription_tier': sub_tier,
            'free_sample_used': False,
        }

    db = get_db()
    created = []
    for idx, template_key in enumerate(templates):
        email_value = alias_email(base_email, template_key, idx)
        created.append(upsert_dev_user(db, email_value, template_key))
    db.commit()

    active_user = created[-1] if created else None
    if active_user:
        session['user_id'] = active_user['id']
        session['profile_id'] = active_user['id']

    payload = {'ok': True, 'created': created}
    if active_user:
        payload['active_user'] = active_user
        payload.update({k: active_user[k] for k in ('id', 'email', 'is_paid', 'free_sample_used')})
    return jsonify(payload)


@app.post('/api/generate')
def api_generate():
    rl = _enforce_rate_limit(f"{request.remote_addr}:generate", capacity=30, refill_seconds=60)
    if rl:
        return rl
    payload = request.get_json(force=True) or {}
    raw_image_data = payload.get('image_data_url')
    image_data_url = None
    if raw_image_data:
        if not isinstance(raw_image_data, str):
            return jsonify({'ok': False, 'error': 'Invalid image payload'}), 400
        if len(raw_image_data) > IMAGE_DATA_URL_MAX_BYTES:
            return jsonify({'ok': False, 'error': 'Image is too large (max 2.5MB encoded)'}), 400
        if raw_image_data.startswith('data:'):
            prefix = raw_image_data[:20].lower()
            if not prefix.startswith('data:image/'):
                return jsonify({'ok': False, 'error': 'Only inline image data URLs are supported'}), 400
        elif not raw_image_data.lower().startswith(('http://', 'https://')):
            return jsonify({'ok': False, 'error': 'Image must be a data URL or HTTPS link'}), 400
        image_data_url = raw_image_data
    profile = _get_active_profile_dict() or {}
    generation = _merge_generation_payload(payload, profile)
    if image_data_url:
        generation['image_data_url'] = image_data_url
    days = generation['days']
    user_row = _get_current_user_row()
    uid = user_row['id'] if user_row else None
    is_paid = bool(user_row and user_row['is_paid'])
    free_sample_used = bool(user_row and user_row['free_sample_used'])

    flags = load_flags()
    gate_paid = bool(flags.get('gate7DayToPaid', False))

    if days > 1 and not uid:
        return jsonify({'ok': False, 'error': 'Sign in required for multi-day plans'}), 401
    if days > 1 and gate_paid and not is_paid:
        return jsonify({'ok': False, 'error': 'Paid subscription required for multi-day plans'}), 403
    if days == 1 and user_row and not is_paid and free_sample_used:
        return jsonify({'ok': False, 'error': 'Free sample already used'}), 403

    wants_reels = _short_video_requested(generation['platforms'])
    if wants_reels:
        if not uid:
            return jsonify({'ok': False, 'error': 'Sign in required for reels'}), 401
        if not is_paid:
            return jsonify({'ok': False, 'error': 'Upgrade required to generate reels'}), 403
        allowed, _ = _check_reels_quota(uid, days)
        if not allowed:
            return jsonify({'ok': False, 'error': 'Monthly reels quota reached'}), 403

    image_attachment = generation.pop('image_data_url', None)
    posts = None
    if image_attachment and USE_OPENAI and openai_client is not None:
        enriched = dict(generation)
        enriched['image_data_url'] = image_attachment
        posts = _generate_posts_from_image(enriched)
    if posts is None and USE_OPENAI and openai_client is not None and generation['days'] <= 7:
        posts = _generate_posts_via_openai(generation)

    if posts is None:
        try:
            posts = generate_posts(
                days=generation['days'],
                start_day=generation['start_day'],
                industry=generation['industry'],
                tone=generation['tone'],
                platforms=generation['platforms'],
                brand_keywords=generation['brand_keywords'],
                include_images=generation['include_images'],
                niche_keywords=generation['niche_keywords'],
                goals=generation['goals'],
                details=generation['details'],
                company=generation['company']
            )
        except Exception:
            return jsonify({'ok': False, 'error': 'Failed to generate content'}), 500

    if days == 1 and user_row and uid and not is_paid and not free_sample_used:
        _mark_free_sample_used(uid)
    if wants_reels and uid:
        _increment_reels_usage(uid, days)

    profile_snapshot = dict(generation)
    profile_snapshot.pop('image_context', None)
    if isinstance(profile_snapshot.get('start_day'), date):
        profile_snapshot['start_day'] = profile_snapshot['start_day'].isoformat()

    return jsonify({'ok': True, 'count': len(posts), 'posts': posts, 'profile': profile_snapshot})


@app.post('/api/generate-variants')
def api_generate_variants():
    rl = _enforce_rate_limit(f"{request.remote_addr}:generate-variants", capacity=20, refill_seconds=60)
    if rl:
        return rl
    env = os.getenv('FLASK_ENV', '').lower()
    if env != 'development' and not _get_current_user_row():
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
    data = request.get_json(force=True) or {}
    industry = (data.get('industry') or 'Business').strip() or 'Business'
    tone = (data.get('tone') or 'friendly').strip() or 'friendly'
    platform = (data.get('platform') or 'instagram').strip() or 'instagram'
    try:
        count = int(data.get('count') or 3)
    except Exception:
        count = 3
    count = max(1, min(count, 10))
    brand_keywords = _coerce_str_list(data.get('brand_keywords'), [])
    goals = _coerce_str_list(data.get('goals'), [])
    variants = []
    for idx in range(count):
        pillar_name, pillar_hint = gen_mod.PILLARS_BY_DEFAULT[idx % len(gen_mod.PILLARS_BY_DEFAULT)]
        caption = gen_mod.make_caption(industry, tone, pillar_name, pillar_hint, platform, brand_keywords, gen_mod.default_hashtags(industry, brand_keywords), goals)
        variants.append({'platform': platform, 'pillar': pillar_name, 'caption': caption})
    return jsonify({'ok': True, 'variants': variants})


@app.post('/api/feedback')
def api_feedback():
    rl = _enforce_rate_limit(f"{request.remote_addr}:feedback", capacity=20, refill_seconds=60)
    if rl:
        return rl
    data = request.get_json(force=True) or {}
    rating = int(data.get('rating') or 0)
    post_day = int(data.get('post_day') or 0)
    platform = (data.get('platform') or '').strip()
    note = (data.get('note') or '').strip()
    source = (data.get('source') or 'dashboard').strip() or 'dashboard'
    post_snapshot = _trim_feedback_text(data.get('post_snapshot') or '', 1600)
    plan_length = data.get('plan_length')
    if plan_length:
        try:
            plan_length = int(plan_length)
        except Exception:
            plan_length = None
    if len(note) > MAX_FEEDBACK_NOTE_LEN:
        note = note[:MAX_FEEDBACK_NOTE_LEN]
    profile_id = session.get('user_id') or session.get('profile_id')
    db = get_db()
    db.execute('INSERT INTO feedback (profile_id, post_day, platform, rating, note) VALUES (?, ?, ?, ?, ?)', (profile_id, post_day or None, platform or None, rating, note or None))
    db.commit()
    issue_info = None
    if rating < 0:
        profile = _get_active_profile_dict() or {}
        user_row = _get_current_user_row()
        issue_context = {
            'summary': data.get('summary') or note or f'{platform} content adjustment',
            'note': note,
            'post_snapshot': post_snapshot,
            'platform': platform,
            'post_day': post_day,
            'source': source,
            'plan_length': plan_length,
            'profile': profile,
            'tone': profile.get('tone') if isinstance(profile, dict) else None,
            'industry': profile.get('industry') if isinstance(profile, dict) else None,
            'user_email': _get_user_email(user_row)
        }
        issue_info = _maybe_create_feedback_issue('thumbs_down', issue_context)
    resp = {'ok': True}
    if issue_info:
        resp['issue_url'] = issue_info.get('html_url')
        resp['issue_number'] = issue_info.get('number')
    return jsonify(resp)


@app.post('/api/feedback/report')
def api_feedback_report():
    rl = _enforce_rate_limit(f"{request.remote_addr}:feedback-report", capacity=10, refill_seconds=60)
    if rl:
        return rl
    user_row = _get_current_user_row()
    if not user_row:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
    data = request.get_json(force=True) or {}
    summary = (data.get('summary') or '').strip()
    details = (data.get('details') or '').strip()
    if not summary or not details:
        return jsonify({'ok': False, 'error': 'Summary and details are required'}), 400
    category = (data.get('category') or 'idea').strip().lower()
    allowed_categories = {'idea', 'bug', 'request'}
    if category not in allowed_categories:
        category = 'idea'
    allow_contact = bool(data.get('allow_contact'))
    plan_length = data.get('plan_length')
    if plan_length:
        try:
            plan_length = int(plan_length)
        except Exception:
            plan_length = None
    note_blob = f"{summary}\n\n{details}"
    if len(note_blob) > MAX_FEEDBACK_NOTE_LEN:
        note_blob = note_blob[:MAX_FEEDBACK_NOTE_LEN]
    profile = _get_active_profile_dict() or {}
    profile_id = session.get('user_id') or session.get('profile_id')
    db = get_db()
    db.execute(
        'INSERT INTO feedback (profile_id, post_day, platform, rating, note) VALUES (?, ?, ?, ?, ?)',
        (profile_id, None, f'general:{category}', 0, note_blob)
    )
    db.commit()
    issue_context = {
        'summary': summary,
        'details': details,
        'category': category,
        'allow_contact': allow_contact,
        'platform': data.get('platform'),
        'plan_length': plan_length,
        'tone': data.get('tone') or profile.get('tone'),
        'industry': data.get('industry') or profile.get('industry'),
        'platforms': profile.get('platforms'),
        'source': data.get('source') or 'settings-panel',
        'profile': profile,
        'user_email': _get_user_email(user_row)
    }
    issue_info = _maybe_create_feedback_issue('general', issue_context)
    resp = {'ok': True}
    if issue_info:
        resp['issue_url'] = issue_info.get('html_url')
        resp['issue_number'] = issue_info.get('number')
    return jsonify(resp)


@app.post('/api/signup')
def api_signup():
    rl = _enforce_rate_limit(f"{request.remote_addr}:signup", capacity=10, refill_seconds=300)
    if rl:
        return rl
    data = request.get_json(force=True) or {}
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({'ok': False, 'error': 'Invalid email'}), 400
    if not password or len(password) < 6:
        return jsonify({'ok': False, 'error': 'Password too short (min 6 chars)'}), 400
    db = get_db()
    uid = str(uuid.uuid4())
    pw_hash = _hash_password(password)
    try:
        db.execute("INSERT INTO users (id, email, password_hash, is_paid, free_sample_used) VALUES (?, ?, ?, 0, 0)", (uid, email, pw_hash))
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'ok': False, 'error': 'Email already registered', 'code': 'email_exists'}), 409
    except Exception:
        app.logger.exception('signup failed')
        return jsonify({'ok': False, 'error': 'Unable to complete signup. Please try again.'}), 500
    session['user_id'] = uid
    session['profile_id'] = uid
    user_payload = {'id': uid, 'email': email, 'is_paid': False, 'free_sample_used': False}
    return jsonify({'ok': True, 'user': user_payload, 'id': uid})


@app.post('/api/generate-review-response')
def api_generate_review_response():
    """Generate a professional response to a customer review."""
    rl = _enforce_rate_limit(f"{request.remote_addr}:review-response", capacity=20, refill_seconds=60)
    if rl:
        return rl
    data = request.get_json(force=True) or {}
    review_text = (data.get('review_text') or '').strip()
    tone = data.get('tone', 'professional')
    company_name = (data.get('company_name') or '').strip()
    industry = (data.get('industry') or '').strip()
    
    if not review_text:
        return jsonify({'ok': False, 'error': 'Review text is required'}), 400
    
    # fall back to saved profile info when available
    profile = _get_active_profile_dict()
    if profile:
        if not industry:
            industry = profile.get('industry', '')
        if not company_name:
            company_name = profile.get('company', '')
    
    try:
        result = gen_mod.generate_review_response(
            review_text=review_text,
            tone=tone,
            company_name=company_name,
            industry=industry
        )
        return jsonify({'ok': True, **result})
    except ValueError as e:
        return jsonify({'ok': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'ok': False, 'error': 'Failed to generate response'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=os.getenv('FLASK_ENV') == 'development', use_reloader=False)
