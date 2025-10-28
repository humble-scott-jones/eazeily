import os, sqlite3, uuid, json, re
from datetime import date
from datetime import datetime, timezone
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, g, session, redirect, has_app_context
import threading
import time
import math
from flask_cors import CORS
import generator as gen_mod
from werkzeug.security import generate_password_hash, check_password_hash
from typing import TYPE_CHECKING

# optional stripe import (only used if STRIPE_SECRET_KEY is set)
try:
    if TYPE_CHECKING:
        # ensure type-checkers know about stripe without requiring it at runtime
        import stripe  # type: ignore
    else:
        import stripe
except Exception:
    stripe = None

USE_OPENAI = bool(os.getenv("OPENAI_API_KEY"))
if USE_OPENAI:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        USE_OPENAI = False

app = Flask(__name__)
_secret = os.getenv("SECRET_KEY")
if not _secret:
    _secret = "dev-secret-change-me"
app.secret_key = _secret
CORS(app)

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

# Simple in-memory token-bucket rate limiter for low-volume dev/prod protection.
# For production, prefer a distributed store (Redis) and a proper rate-limiting middleware.
RATE_LIMIT_STORE = {}
RATE_LIMIT_LOCK = threading.Lock()

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

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
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
            pw_hash = generate_password_hash(dev_pw, method='pbkdf2:sha256')
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

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring and load balancers"""
    health_status = {
        'status': 'healthy',
        'version': os.getenv('APP_VERSION', 'dev'),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'checks': {}
    }
    
    # Check database connectivity
    try:
        db = get_db()
        result = db.execute('SELECT 1').fetchone()
        if result is not None:
            health_status['checks']['database'] = 'connected'
        else:
            health_status['checks']['database'] = 'disconnected'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['database'] = 'disconnected'
        health_status['status'] = 'unhealthy'
    
    # Check Stripe availability (if configured)
    if os.getenv('STRIPE_SECRET_KEY') and stripe:
        health_status['checks']['stripe'] = 'configured'
    else:
        health_status['checks']['stripe'] = 'not_configured'
    
    # Check OpenAI availability (if configured)
    if USE_OPENAI:
        health_status['checks']['openai'] = 'configured'
    else:
        health_status['checks']['openai'] = 'not_configured'
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code



@app.get("/")
def landing():
    """Landing page with marketing content, pricing, and waitlist signup."""
    return render_template("landing.html")

@app.get("/app")
def index():
    """Main application page for authenticated users."""
    is_dev = os.getenv('FLASK_ENV') == 'development' or os.getenv('ALLOW_DEV_DEBUG') == '1'
    return render_template("index.html", is_dev=is_dev)


@app.get('/review-response')
def review_response_page():
    """Page for generating responses to customer reviews."""
    return render_template("review_response.html")


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
    subscription = row_to_mapping(sub) if sub else None
    # try to fetch fresh data from Stripe and enrich with human dates (best-effort)
    try:
        if subscription and stripe and os.getenv('STRIPE_SECRET_KEY') and subscription.get('stripe_subscription_id'):
            stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
            remote = stripe.Subscription.retrieve(subscription['stripe_subscription_id'])
            subscription['status'] = remote.get('status')
            subscription['current_period_end'] = remote.get('current_period_end')
    except Exception:
        pass
    # enrich human-friendly date similar to /api/account
    if subscription and subscription.get('current_period_end'):
        try:
            cpe = subscription.get('current_period_end')
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
    # pass is_admin flag to template for rendering admin controls
    return render_template('account.html', user=user, subscription=subscription, is_admin=is_admin())


@app.get('/api/account')
def api_account():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Not authenticated'}), 401
    db = get_db()
    user = db.execute('SELECT id, email, is_paid, stripe_customer_id FROM users WHERE id = ?', (uid,)).fetchone()
    sub = db.execute('SELECT id, stripe_subscription_id, status, current_period_end FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1', (uid,)).fetchone()
    subscription_data = row_to_mapping(sub) if sub else None
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
        return jsonify({'ok': True, 'job': row_to_mapping(row)})
    else:
        t = threading.Thread(target=run_job, args=(job_id,))
        t.daemon = True
        t.start()
        return jsonify({'ok': True, 'job_id': job_id})


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


@app.post('/api/signup')
def api_signup():
    data = request.get_json(force=True)
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({'ok': False, 'error': 'Invalid email'}), 400
    if not password or len(password) < 6:
        return jsonify({'ok': False, 'error': 'Password too short (min 6 chars)'}), 400
    db = get_db()
    uid = str(uuid.uuid4())
    pw = generate_password_hash(password, method='pbkdf2:sha256')
    try:
        db.execute("INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)", (uid, email, pw))
        db.commit()
    except Exception as e:
        return jsonify({'ok': False, 'error': 'Email already registered'}), 400
    session['user_id'] = uid
    return jsonify({'ok': True, 'id': uid, 'email': email, 'is_paid': False, 'free_sample_used': False})

*** End Patch