import os, sqlite3, uuid, json, re
from datetime import date
from datetime import datetime, timezone
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, g, session
import threading
import time
from flask_cors import CORS
import generator
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
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-me")
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), "togetherly.db")


def dev_mode_active() -> bool:
    """Return True when tests/dev helpers should bypass certain production checks."""
    if app.config.get('TESTING'):
        return True
    if os.getenv('ALLOW_DEV_DEBUG') == '1':
        return True
    if os.getenv('PYTEST_CURRENT_TEST'):
        return True
    return False


def admin_bypass_allowed() -> bool:
    """Only allow admin guard bypass when explicit dev debug flag is enabled."""
    if app.config.get('TESTING'):
        return False
    if os.getenv('PYTEST_CURRENT_TEST'):
        return False
    return os.getenv('ALLOW_DEV_DEBUG') == '1'


def coerce_bool(value, default=False) -> bool:
    """Convert loosely-typed truthy values into a strict boolean."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
        return default
    return bool(value)


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
            reels_generated INTEGER DEFAULT 0,
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

@app.get("/")
def index():
    is_dev = os.getenv('FLASK_ENV') == 'development' or os.getenv('ALLOW_DEV_DEBUG') == '1'
    return render_template("index.html", is_dev=is_dev)


@app.get('/account')
def account_page():
    uid = session.get('user_id')
    if not uid:
        return render_template('account.html', user=None)
    db = get_db()
    user = db.execute('SELECT id, email, is_paid, stripe_customer_id FROM users WHERE id = ?', (uid,)).fetchone()
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


def generate_posts_with_openai(
    *,
    days: int,
    start_day: date,
    industry: str,
    tone: str,
    platforms: list[str],
    brand_keywords: list[str],
    include_images: bool,
    niche_keywords: list[str],
    goals: list[str],
    details: dict,
    company: str,
):
    if not USE_OPENAI:
        return None

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system_prompt = (
        "You are a senior social media strategist and influencer-style copywriter. "
        "Write platform-specific content that sounds human, scroll-stopping, and on-brand. "
        "Respect the requested tone and business context. Use provided brand/niche keywords naturally (no stuffing). "
        "Optimize for the stated goals (e.g., drive sales, build authority, engagement). "
        "For platforms that support short-form video, include a concise reel plan with a strong hook, clear beats, on-screen text, and a single specific CTA. "
        "Always return ONLY JSON that matches the schema—no prose."
    )

    schedule = [
        {
            "day_index": idx + 1,
            "date": (start_day + timedelta(days=idx)).isoformat(),
            "platforms": platforms,
        }
        for idx in range(days)
    ]
    pillar_labels = [p[0] for p in generator.PILLARS_BY_DEFAULT]
    industry_context = generator.build_industry_context(
        industry,
        brand_keywords,
        niche_keywords,
        details,
        goals,
        company,
    )
    payload = {
        "industry": industry,
        "tone": tone,
        "company": company,
        "brand_keywords": brand_keywords,
        "niche_keywords": niche_keywords,
        "goals": goals,
        "details": details or {},
        "include_images": include_images,
        "platforms": platforms,
        "schedule": schedule,
        "allowed_pillars": pillar_labels,
        "reel_platforms": ["instagram", "tiktok", "short_video"],
        "industry_context": industry_context,
        "industry_key": industry_context.get("industry_key"),
    }

    json_schema = {
        "type": "object",
        "properties": {
            "posts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "day_index": {"type": "integer"},
                        "platform": {"type": "string"},
                        "pillar": {"type": "string"},
                        "caption": {"type": "string"},
                        "image_prompt": {"type": "string"},
                        "image_url": {"type": ["string", "null"]},
                        "reel": {
                            "type": ["object", "null"],
                            "properties": {
                                "style": {"type": "string"},
                                "hook": {"type": "string"},
                                "script_beats": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "shot_list": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "shot_type": {"type": "string"},
                                            "notes": {"type": "string"},
                                        },
                                        "required": ["shot_type", "notes"],
                                    },
                                },
                                "on_screen_text": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                                "thumbnail_prompt": {"type": "string"},
                                "srt": {"type": "string"},
                                "cta": {"type": "string"},
                                "hashtags": {
                                    "type": "object",
                                    "properties": {
                                        "primary": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                        "optional": {
                                            "type": "array",
                                            "items": {"type": "string"},
                                        },
                                    },
                                },
                            },
                        },
                    },
                    "required": ["date", "day_index", "platform", "pillar", "caption"],
                },
            }
        },
        "required": ["posts"],
    }

    try:
        responses_api = getattr(openai_client, "responses", None)
        if responses_api is None:
            raise ValueError("OpenAI client is missing the responses API")

        response = responses_api.create(
            model=model,
            input=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": (
                        "Create social content for the provided business. "
                        "Return only JSON matching the schema. "
                        "Each day must include one post per requested platform. "
                        "Captions should be specific, compelling, and end with hashtags when helpful. "
                        "Write in an easy-to-consume style: short sentences, skimmable structure, and clear value in the first line while keeping the polish of an experienced influencer. "
                        "Highlight key details with crisp formatting (line breaks, emoji if appropriate) so busy readers can grab the takeaway fast. "
                        "If a platform supports reels (instagram, tiktok, short_video) include a reel plan; otherwise set reel to null."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "social_media_plan",
                    "schema": json_schema,
                },
            },
        )

        raw_output = getattr(response, "output_text", None)
        if not raw_output:
            chunks: list[str] = []
            for block in getattr(response, "output", []) or []:
                for part in getattr(block, "content", []) or []:
                    if getattr(part, "type", "") == "output_text":
                        chunks.append(getattr(part, "text", ""))
            raw_output = "".join(chunks)
        if not raw_output:
            raise ValueError("Empty OpenAI response")

        parsed = json.loads(raw_output)
        posts = parsed.get("posts")
        if not isinstance(posts, list) or not posts:
            raise ValueError("OpenAI response missing posts")

        platforms_lower = [p.lower() for p in platforms]
        expected_count = days * len(platforms_lower)
        normalized: list[dict] = []
        for entry in posts:
            if not isinstance(entry, dict):
                continue

            platform_raw = str(entry.get("platform", "")).strip().lower()
            platform = platform_raw
            if platform not in platforms_lower:
                if "instagram" in platform_raw:
                    platform = "instagram"
                elif "tiktok" in platform_raw:
                    platform = "tiktok"
                elif "facebook" in platform_raw:
                    platform = "facebook"
                elif "linkedin" in platform_raw:
                    platform = "linkedin"
                elif platform_raw in {"x", "twitter"}:
                    platform = "twitter"
            if platform not in platforms_lower:
                continue

            day_index_value = entry.get("day_index")
            try:
                day_index = int(day_index_value)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                day_index = None

            date_str = str(entry.get("date", "")).strip()
            parsed_day = None
            if date_str:
                try:
                    parsed_day = datetime.fromisoformat(date_str).date()
                except Exception:
                    parsed_day = None
            if parsed_day is not None:
                computed_index = (parsed_day - start_day).days + 1
                if 1 <= computed_index <= days:
                    day_index = computed_index
            if day_index is None or not (1 <= day_index <= days):
                continue
            if not date_str:
                date_str = (start_day + timedelta(days=day_index - 1)).isoformat()

            pillar = (entry.get("pillar") or "Story").strip() or "Story"
            # nudge pillar into allowed set when possible
            for label in pillar_labels:
                if pillar.lower().startswith(label.lower()[:5]):
                    pillar = label
                    break

            caption = str(entry.get("caption", "")).strip()
            if not caption:
                continue
            if "#" not in caption:
                tags = generator.default_hashtags(industry, niche_keywords)
                if tags:
                    caption = caption + ("\n\n" if caption else "") + " ".join(tags[:8])

            image_prompt_text = str(entry.get("image_prompt") or "").strip()
            if not image_prompt_text:
                image_prompt_text = generator.image_prompt(industry, pillar, brand_keywords, company)

            image_url = None
            if include_images:
                image_url_raw = entry.get("image_url")
                if isinstance(image_url_raw, str) and image_url_raw.strip():
                    image_url = image_url_raw.strip()
                else:
                    image_url = generator.unsplash_link(industry, pillar)

            reel_data = entry.get("reel") if platform in payload["reel_platforms"] else None
            if reel_data and isinstance(reel_data, dict):
                shot_list = reel_data.get("shot_list")
                normalized_shots: list[dict] = []
                if isinstance(shot_list, list):
                    for item in shot_list:
                        if isinstance(item, dict):
                            shot_type = str(item.get("shot_type") or item.get("type") or "").strip()
                            notes = str(item.get("notes") or item.get("description") or "").strip()
                            if shot_type:
                                normalized_shots.append({"shot_type": shot_type, "notes": notes})
                        elif isinstance(item, str) and item.strip():
                            normalized_shots.append({"shot_type": item.strip(), "notes": ""})
                reel_data["shot_list"] = normalized_shots

                hashtags_field = reel_data.get("hashtags")
                if isinstance(hashtags_field, list):
                    reel_data["hashtags"] = {
                        "primary": [h for h in hashtags_field[:4] if isinstance(h, str)],
                        "optional": [h for h in hashtags_field[4:8] if isinstance(h, str)],
                    }
            else:
                reel_data = None

            normalized.append(
                {
                    "date": date_str,
                    "day_index": day_index,
                    "platform": platform,
                    "pillar": pillar,
                    "caption": caption,
                    "image_prompt": image_prompt_text,
                    "image_url": image_url if include_images else None,
                    "reel": reel_data,
                }
            )

        deduped: dict[tuple[int, str], dict] = {}
        for post in normalized:
            key = (post["day_index"], post["platform"])
            if key not in deduped:
                deduped[key] = post

        normalized = list(deduped.values())
        platforms_lower_lookup = {p: idx for idx, p in enumerate(platforms_lower)}
        normalized.sort(key=lambda p: (p["day_index"], platforms_lower_lookup.get(p["platform"], 999)))

        if len(normalized) != expected_count:
            raise ValueError(
                f"OpenAI returned {len(normalized)} posts, expected {expected_count}"
            )

        return normalized
    except Exception as exc:
        app.logger.warning("OpenAI generation failed: %s", exc)
        return None


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
    # Helper used in tests; allow calling outside an application context by
    # opening a direct sqlite connection if needed.
    try:
        db = get_db()
        return db.execute('SELECT * FROM users WHERE email = ?', (email.lower(),)).fetchone()
    except RuntimeError:
        # Working outside app context: open a temporary connection directly to DB_PATH
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
        db = get_db()
        return db.execute('SELECT * FROM users WHERE id = ?', (uid,)).fetchone()
    except RuntimeError:
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

def set_user_paid(uid: str, paid: bool = True, db=None):
    target_db = db or get_db()
    try:
        target_db.execute('UPDATE users SET is_paid = ? WHERE id = ?', (1 if paid else 0, uid))
        target_db.commit()
    except Exception:
        pass


def sync_subscription_state(uid: str, db=None):
    """Best-effort sync of the latest Stripe subscription state.

    Returns True if the user was marked paid during this call.
    """
    target_db = db or get_db()
    sub = target_db.execute(
        'SELECT id, stripe_subscription_id, status FROM subscriptions WHERE user_id = ? ORDER BY created_at DESC LIMIT 1',
        (uid,),
    ).fetchone()
    if not sub:
        return False

    status = sub['status']
    if status in ('active', 'trialing'):
        set_user_paid(uid, True, db=target_db)
        return True

    stripe_sub_id = sub['stripe_subscription_id']
    if not stripe_sub_id or stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return False

    try:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        remote = stripe.Subscription.retrieve(stripe_sub_id)
        status = remote.get('status')
        cpe = remote.get('current_period_end')
        target_db.execute(
            'UPDATE subscriptions SET status = ?, current_period_end = ? WHERE id = ?',
            (status, cpe, sub['id'])
        )
        target_db.commit()
        if status in ('active', 'trialing'):
            set_user_paid(uid, True, db=target_db)
            return True
    except Exception:
        pass
    return False


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


@app.post('/api/login')
def api_login():
    data = request.get_json(force=True)
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''
    db = get_db()
    row = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if not row or not check_password_hash(row['password_hash'] or '', password):
        return jsonify({'ok': False, 'error': 'Invalid credentials'}), 401
    session['user_id'] = row['id']
    free_sample_used = bool(row['free_sample_used']) if 'free_sample_used' in row.keys() else False
    return jsonify({'ok': True, 'id': row['id'], 'email': row['email'], 'is_paid': bool(row['is_paid']), 'free_sample_used': free_sample_used})


@app.post('/api/logout')
def api_logout():
    session.pop('user_id', None)
    return jsonify({'ok': True})


@app.get('/api/current_user')
def api_current_user():
    uid = session.get('user_id')
    if not uid:
        return jsonify({})
    db = get_db()
    row = db.execute('SELECT id, email, is_paid, free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
    if not row:
        return jsonify({})
    if not bool(row['is_paid']):
        if sync_subscription_state(uid, db=db):
            row = db.execute('SELECT id, email, is_paid, free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
    return jsonify({'id': row['id'], 'email': row['email'], 'is_paid': bool(row['is_paid']), 'free_sample_used': bool(row['free_sample_used'])})


@app.post('/api/create-checkout-session')
def api_create_checkout():
    # creates a Stripe Checkout Session for the current user; requires STRIPE_SECRET_KEY
    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured. Set STRIPE_SECRET_KEY in env for test mode.'}), 501
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Authentication required'}), 401
    data = request.get_json(force=True)
    # prefer STRIPE_PRICE_ID (canonical) but fall back to legacy STRIPE_TEST_PRICE_ID
    price_id = data.get('price_id') or os.getenv('STRIPE_PRICE_ID') or os.getenv('STRIPE_TEST_PRICE_ID')
    if not price_id:
        return jsonify({'ok': False, 'error': 'No price configured. Set STRIPE_TEST_PRICE_ID or pass price_id.'}), 400
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    try:
        # in test mode create a session and return the URL
        sess = stripe.checkout.Session.create(
            mode='subscription',
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=os.getenv('STRIPE_SUCCESS_URL', 'http://localhost:5001/'),
            cancel_url=os.getenv('STRIPE_CANCEL_URL', 'http://localhost:5001/'),
            client_reference_id=uid
        )
        return jsonify({'ok': True, 'url': sess.url})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.post('/api/stripe-webhook')
def api_stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    event = None
    db = get_db()
    # Treat placeholder webhook secret values (e.g. from .env templates) as "not configured"
    # so local/dev environments can post plain JSON without signature verification.
    dev_override = admin_bypass_allowed()
    secret_configured = bool(secret) and stripe and not (isinstance(secret, str) and secret.strip().upper().startswith('WHSEC_REPLACE'))
    if dev_override:
        secret_configured = False
    if secret_configured:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
        except Exception as e:
            # invalid signature
            return jsonify({'ok': False, 'error': 'invalid signature'}), 400
    else:
        # fallback: try to parse JSON without verification (local dev)
        try:
            event = json.loads(payload)
        except Exception:
            return jsonify({'ok': False}), 400

    typ = event.get('type')
    data = event.get('data', {}).get('object', {})

    # Handle checkout.session.completed: mark user paid and store subscription id
    if typ == 'checkout.session.completed':
        client_ref = data.get('client_reference_id')
        customer = data.get('customer')
        subscription_id = data.get('subscription')
        if client_ref:
            try:
                db.execute('UPDATE users SET stripe_customer_id = ?, is_paid = 1 WHERE id = ?', (customer, client_ref))
                # create subscription row if subscription_id present
                if subscription_id:
                    sub_id = str(uuid.uuid4())
                    db.execute('INSERT OR REPLACE INTO subscriptions (id, user_id, stripe_subscription_id, status) VALUES (?, ?, ?, ?)',
                               (sub_id, client_ref, subscription_id, 'active'))
                db.commit()
            except Exception:
                pass

    # Handle subscription lifecycle events to update status
    if typ in ('customer.subscription.created', 'customer.subscription.updated', 'customer.subscription.deleted'):
        sub = data
        stripe_sub_id = sub.get('id')
        status = sub.get('status')
        customer = sub.get('customer')
        # try to find user by stripe_customer_id
        user_row = db.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (customer,)).fetchone()
        if user_row:
            uid = user_row['id']
            # upsert subscription
            try:
                # find existing
                existing = db.execute('SELECT id FROM subscriptions WHERE stripe_subscription_id = ?', (stripe_sub_id,)).fetchone()
                if existing:
                    db.execute('UPDATE subscriptions SET status = ?, current_period_end = ? WHERE id = ?', (status, sub.get('current_period_end'), existing['id']))
                else:
                    db.execute('INSERT INTO subscriptions (id, user_id, stripe_subscription_id, status, current_period_end) VALUES (?, ?, ?, ?, ?)',
                               (str(uuid.uuid4()), uid, stripe_sub_id, status, sub.get('current_period_end')))
                # set user paid flag based on status
                is_paid = 1 if status in ('active', 'trialing') else 0
                db.execute('UPDATE users SET is_paid = ? WHERE id = ?', (is_paid, uid))
                db.commit()
            except Exception:
                pass

    # invoice payment succeeded -> ensure user is marked paid
    if typ == 'invoice.payment_succeeded':
        inv = data
        customer = inv.get('customer')
        user_row = db.execute('SELECT id FROM users WHERE stripe_customer_id = ?', (customer,)).fetchone()
        if user_row:
            try:
                db.execute('UPDATE users SET is_paid = 1 WHERE id = ?', (user_row['id'],))
                db.commit()
            except Exception:
                pass

    return jsonify({'ok': True})


@app.post('/api/create-portal-session')
def api_create_portal():
    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured'}), 501
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Authentication required'}), 401
    db = get_db()
    user = db.execute('SELECT stripe_customer_id FROM users WHERE id = ?', (uid,)).fetchone()
    if not user or not user['stripe_customer_id']:
        return jsonify({'ok': False, 'error': 'No stripe customer for user'}), 400
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    try:
        sess = stripe.billing_portal.Session.create(customer=user['stripe_customer_id'], return_url=os.getenv('STRIPE_MANAGE_URL', 'http://localhost:5001/'))
        return jsonify({'ok': True, 'url': sess.url})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.get('/api/stripe-publishable-key')
def api_stripe_publishable_key():
    """Return the Stripe publishable key for client-side Stripe.js initialization."""
    if not os.getenv('STRIPE_PUBLISHABLE_KEY'):
        return jsonify({'ok': False, 'error': 'Publishable key not configured'}), 501
    return jsonify({'ok': True, 'publishableKey': os.getenv('STRIPE_PUBLISHABLE_KEY')})


@app.get('/api/stripe-price')
def api_stripe_price():
    """Return a small JSON object describing the configured Stripe Price (amount/currency/interval, product name).

    Uses STRIPE_TEST_PRICE_ID if no price_id query param is provided. Returns 501 if Stripe isn't configured.
    """
    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured'}), 501
    # prefer STRIPE_PRICE_ID (canonical) but fall back to legacy STRIPE_TEST_PRICE_ID
    price_id = request.args.get('price_id') or os.getenv('STRIPE_PRICE_ID') or os.getenv('STRIPE_TEST_PRICE_ID')
    if not price_id:
        return jsonify({'ok': False, 'error': 'No price_id configured'}), 400
    try:
        stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
        price = stripe.Price.retrieve(price_id)
        # amount is typically in cents (unit_amount)
        unit = price.get('unit_amount') or price.get('unit_amount_decimal')
        currency = price.get('currency') or 'usd'
        recurring = price.get('recurring') or {}
        interval = recurring.get('interval') if recurring else None
        # nice display string (e.g. "$9 / month")
        display = None
        try:
            if unit is not None:
                amt = int(unit) / 100.0
                # show as integer dollars when whole dollars
                display = f"${amt:.0f}" if (amt).is_integer() else f"${amt:.2f}"
                if interval:
                    display = f"{display} / {interval}"
        except Exception:
            display = None
        product_obj = None
        product_id = price.get('product')
        if product_id:
            try:
                prod = stripe.Product.retrieve(product_id)
                product_obj = {'id': prod.get('id'), 'name': prod.get('name')}
            except Exception:
                product_obj = None
        return jsonify({'ok': True, 'price': {'id': price.get('id'), 'unit_amount': unit, 'currency': currency, 'interval': interval, 'display': display, 'product': product_obj}})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.post('/api/create-subscription')
def api_create_subscription():
    """Create or update Stripe Customer, attach payment method, and create a subscription.

    Expects JSON: { price_id, payment_method }
    Returns: { ok: True, client_secret?, subscription_id, status }
    """
    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured'}), 501
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Authentication required'}), 401
    data = request.get_json(force=True)
    # prefer STRIPE_PRICE_ID (canonical) but fall back to legacy STRIPE_TEST_PRICE_ID
    price_id = data.get('price_id') or os.getenv('STRIPE_PRICE_ID') or os.getenv('STRIPE_TEST_PRICE_ID')
    payment_method = data.get('payment_method')
    if not price_id:
        return jsonify({'ok': False, 'error': 'price_id required'}), 400
    if not payment_method:
        return jsonify({'ok': False, 'error': 'payment_method required'}), 400

    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    db = get_db()
    user = db.execute('SELECT id, email, stripe_customer_id FROM users WHERE id = ?', (uid,)).fetchone()
    try:
        # sqlite3.Row doesn't implement .get(); convert to mapping-style access
        customer_id = user['stripe_customer_id'] if user and 'stripe_customer_id' in user.keys() else None
        if not customer_id:
            # create customer (pass email only if available)
            cust_kwargs = {}
            try:
                if user and 'email' in user.keys() and user['email']:
                    cust_kwargs['email'] = user['email']
            except Exception:
                pass
            cust = stripe.Customer.create(**cust_kwargs)
            customer_id = cust['id']
            try:
                db.execute('UPDATE users SET stripe_customer_id = ? WHERE id = ?', (customer_id, uid))
                db.commit()
            except Exception:
                pass

        # attach payment method to customer
        try:
            stripe.PaymentMethod.attach(payment_method, customer=customer_id)
        except Exception:
            # ignore if already attached or other recoverable error
            pass
        # set as default payment method for invoices
        try:
            stripe.Customer.modify(customer_id, invoice_settings={'default_payment_method': payment_method})
        except Exception:
            pass

        # create subscription in incomplete state so we can handle SCA if needed
        sub = stripe.Subscription.create(
            customer=customer_id,
            items=[{'price': price_id}],
            payment_behavior='default_incomplete',
            expand=['latest_invoice.payment_intent'],
            payment_settings={'save_default_payment_method': 'on_subscription'}
        )

        # persist subscription locally (upsert on stripe_subscription_id)
        sub_status = sub.get('status')
        sub_cpe = sub.get('current_period_end')
        try:
            existing = db.execute('SELECT id FROM subscriptions WHERE stripe_subscription_id = ?', (sub['id'],)).fetchone()
            if existing:
                db.execute('UPDATE subscriptions SET status = ?, current_period_end = ?, user_id = ? WHERE id = ?',
                           (sub_status, sub_cpe, uid, existing['id']))
            else:
                db.execute('INSERT INTO subscriptions (id, user_id, stripe_subscription_id, status, current_period_end) VALUES (?, ?, ?, ?, ?)',
                           (str(uuid.uuid4()), uid, sub['id'], sub_status, sub_cpe))
            db.commit()
        except Exception:
            # ignore duplicate/insert errors
            pass

        client_secret = None
        latest_invoice = sub.get('latest_invoice') or {}
        payment_intent = latest_invoice.get('payment_intent') or {}
        client_secret = payment_intent.get('client_secret')
        is_paid_now = False
        try:
            if sub_status in ('active', 'trialing'):
                set_user_paid(uid, True, db=db)
                is_paid_now = True
            elif payment_intent.get('status') == 'succeeded':
                set_user_paid(uid, True, db=db)
                is_paid_now = True
            else:
                is_paid_now = sync_subscription_state(uid, db=db)
        except Exception:
            pass

        return jsonify({'ok': True, 'subscription_id': sub['id'], 'status': sub_status, 'client_secret': client_secret, 'is_paid': bool(is_paid_now)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@app.post('/api/reconcile-subscriptions')
def api_reconcile_subscriptions():
    """Admin/dev endpoint: fetch subscription state from Stripe for all local subscription rows
    that have a stripe_subscription_id and upsert the latest status/current_period_end into DB.
    Requires STRIPE_SECRET_KEY to be set and will return 501 if not configured.
    """
    # If ADMIN_EMAILS is set, require the current user to be an admin and validate CSRF token.
    # Treat placeholder ADMIN_EMAILS values (from .env templates) as not configured.
    raw_admin_emails = os.getenv('ADMIN_EMAILS', '') or ''
    admin_emails = raw_admin_emails.strip()
    admin_enabled = False
    if admin_emails and 'REPLACE' not in admin_emails.upper():
        admin_enabled = True
    dev_override = admin_bypass_allowed()
    # Persist state for pytest assertions when running in TESTING mode.
    admin_state = {
        'enabled': admin_enabled,
        'dev_override': dev_override,
        'is_admin': is_admin(),
        'user_id': session.get('user_id'),
    }
    if app.config.get('TESTING'):
        app.config['LAST_RECONCILE_DEBUG'] = admin_state
    if admin_enabled and not (dev_override or admin_state['is_admin']):
        return jsonify({'ok': False, 'error': 'Admin required'}), 403
    # If admin protection is enabled, require a matching CSRF token in a header unless dev override is on
    if admin_enabled and not dev_override:
        token = request.headers.get('X-CSRF-Token')
        if not token or token != session.get('admin_csrf'):
            return jsonify({'ok': False, 'error': 'CSRF token required'}), 403
    if stripe is None or not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'ok': False, 'error': 'Stripe not configured'}), 501
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
    db = get_db()
    rows = db.execute('SELECT id, user_id, stripe_subscription_id FROM subscriptions WHERE stripe_subscription_id IS NOT NULL').fetchall()
    results = []
    for r in rows:
        sid = r['stripe_subscription_id']
        try:
            remote = stripe.Subscription.retrieve(sid)
            status = remote.get('status')
            cpe = remote.get('current_period_end')
            # upsert the values into subscriptions table
            db.execute('UPDATE subscriptions SET status = ?, current_period_end = ? WHERE id = ?', (status, cpe, r['id']))
            # update user is_paid based on status
            is_paid = 1 if status in ('active', 'trialing') else 0
            db.execute('UPDATE users SET is_paid = ? WHERE id = ?', (is_paid, r['user_id']))
            results.append({'id': r['id'], 'stripe_subscription_id': sid, 'status': status})
        except Exception as e:
            results.append({'id': r['id'], 'stripe_subscription_id': sid, 'error': str(e)})
    db.commit()
    return jsonify({'ok': True, 'results': results})


@app.get('/admin')
def admin_page():
    # basic admin interface to trigger reconciliation
    if not is_admin():
        return render_template('admin.html', allowed=False)
    return render_template('admin.html', allowed=True)


# Dev debug route to inspect session and current user (only in dev or when ALLOW_DEV_DEBUG=1)
@app.get('/__debug__/session')
def debug_session():
    if os.getenv('FLASK_ENV') != 'development' and os.getenv('ALLOW_DEV_DEBUG') != '1':
        return jsonify({'ok': False, 'error': 'Not allowed'}), 403
    out = {'session': dict(session)}
    uid = session.get('user_id')
    if uid:
        try:
            db = get_db()
            row = db.execute('SELECT id, email, is_paid FROM users WHERE id = ?', (uid,)).fetchone()
            out['current_user'] = row_to_mapping(row) if row else {}
        except Exception:
            out['current_user'] = {}
    return jsonify({'ok': True, 'debug': out})


# Dev helper: list registered routes (dev-only)
@app.get('/__dev__/routes')
def dev_list_routes():
    if os.getenv('FLASK_ENV') != 'development' and os.getenv('ALLOW_DEV_DEBUG') != '1':
        return jsonify({'ok': False, 'error': 'Not allowed'}), 403
    rules = []
    for rule in app.url_map.iter_rules():
        methods = list(rule.methods) if rule.methods else []
        rules.append({'rule': str(rule), 'endpoint': rule.endpoint, 'methods': sorted(methods)})
    return jsonify({'ok': True, 'routes': rules})


# Dev helper: simple ping
@app.get('/__dev__/ping')
def dev_ping():
    if os.getenv('FLASK_ENV') != 'development' and os.getenv('ALLOW_DEV_DEBUG') != '1':
        return 'Not allowed', 403
    return 'pong'


@app.post('/__dev__/shutdown')
def dev_shutdown():
    if not dev_mode_active():
        return jsonify({'ok': False, 'error': 'Not allowed'}), 403
    shutdown_fn = request.environ.get('werkzeug.server.shutdown')
    if not shutdown_fn:
        return jsonify({'ok': False, 'error': 'Shutdown not available'}), 500
    shutdown_fn()
    return jsonify({'ok': True})


# Dev-only helper: create or update a user and sign them in (only in dev)
@app.post('/__dev__/create_user')
def dev_create_user():
    if os.getenv('FLASK_ENV') != 'development' and os.getenv('ALLOW_DEV_DEBUG') != '1':
        return jsonify({'ok': False, 'error': 'Not allowed'}), 403
    data = request.get_json(force=True)
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or 'password'
    is_paid = coerce_bool(data.get('is_paid'), default=False)
    free_sample_used = coerce_bool(data.get('free_sample_used'), default=False)
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return jsonify({'ok': False, 'error': 'Invalid email'}), 400
    db = get_db()
    # if exists, update password and paid flag, else create
    row = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    uid = row['id'] if row else str(uuid.uuid4())
    pw_hash = generate_password_hash(password, method='pbkdf2:sha256')
    try:
        if row:
            db.execute('UPDATE users SET password_hash = ?, is_paid = ?, free_sample_used = ? WHERE id = ?', (pw_hash, 1 if is_paid else 0, 1 if free_sample_used else 0, uid))
        else:
            db.execute('INSERT INTO users (id, email, password_hash, is_paid, free_sample_used) VALUES (?, ?, ?, ?, ?)', (uid, email, pw_hash, 1 if is_paid else 0, 1 if free_sample_used else 0))
        db.commit()
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
    session['user_id'] = uid
    try:
        row = db.execute('SELECT id, email, is_paid, free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
    except Exception:
        row = None
    payload = {
        'ok': True,
        'id': uid,
        'email': email,
        'is_paid': bool(row['is_paid']) if row else is_paid,
        'free_sample_used': bool(row['free_sample_used']) if row and 'free_sample_used' in row.keys() else free_sample_used
    }
    return jsonify(payload)


@app.post('/api/request-password-reset')
def api_request_password_reset():
    data = request.get_json(force=True)
    email = (data.get('email') or '').strip().lower()
    if not email:
        return jsonify({'ok': False, 'error': 'Email required'}), 400
    db = get_db()
    row = db.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
    if not row:
        # don't leak user existence in production — here we return ok for dev
        return jsonify({'ok': True})
    token = str(uuid.uuid4())
    # token valid for 1 hour
    import datetime
    expires = (datetime.datetime.utcnow() + datetime.timedelta(hours=1)).isoformat()
    try:
        db.execute('INSERT INTO password_reset_tokens (token, user_id, expires_at) VALUES (?, ?, ?)', (token, row['id'], expires))
        db.commit()
    except Exception:
        pass
    # In production, send email with reset link that contains token. For local dev, return token so tests can use it.
    return jsonify({'ok': True, 'token': token})


@app.post('/api/confirm-password-reset')
def api_confirm_password_reset():
    data = request.get_json(force=True)
    token = data.get('token')
    new_pw = data.get('password')
    if not token or not new_pw or len(new_pw) < 6:
        return jsonify({'ok': False, 'error': 'Invalid token or password too short'}), 400
    db = get_db()
    row = db.execute('SELECT * FROM password_reset_tokens WHERE token = ?', (token,)).fetchone()
    if not row:
        return jsonify({'ok': False, 'error': 'Invalid or expired token'}), 400
    import datetime
    if row['expires_at'] and datetime.datetime.fromisoformat(row['expires_at']) < datetime.datetime.utcnow():
        return jsonify({'ok': False, 'error': 'Token expired'}), 400
    # update password
    pw_hash = generate_password_hash(new_pw, method='pbkdf2:sha256')
    try:
        db.execute('UPDATE users SET password_hash = ? WHERE id = ?', (pw_hash, row['user_id']))
        db.execute('DELETE FROM password_reset_tokens WHERE token = ?', (token,))
        db.commit()
    except Exception as e:
        return jsonify({'ok': False, 'error': 'Could not reset password'}), 500
    return jsonify({'ok': True})



@app.post("/api/profile")
def save_profile():
    data = request.get_json(force=True)
    profile_id = session.get("profile_id") or str(uuid.uuid4())
    session["profile_id"] = profile_id

    platforms = data.get("platforms", ["instagram"])
    company = data.get("company", "")
    # normalize company: trim and title-case for consistency
    if isinstance(company, str):
        company = company.strip()
        company = company.title() if company else ""

    # server-side validation: length and allowed chars
    if company:
        if len(company) > 100:
            return jsonify({"ok": False, "error": "Company name is too long (max 100 chars).", "errors": {"company": "Company name is too long (max 100 chars)."}}), 400
        import re
        if not re.match(r"^[\w \-\'\.\&]+$", company):
            return jsonify({"ok": False, "error": "Company name contains invalid characters.", "errors": {"company": "Company name contains invalid characters."}}), 400
    details = data.get("details", {}) or {}
    industry_key = data.get("industry_key")
    if not isinstance(details, dict):
        details = {}
    if industry_key:
        details["_industry_key"] = industry_key
    row = (
        profile_id,
        data.get("industry", "Business"),
        data.get("tone", "friendly"),
        json.dumps(platforms),
        json.dumps(data.get("brand_keywords", [])),
        json.dumps(data.get("niche_keywords", [])),
        json.dumps(data.get("goals", [])),
        json.dumps(details),
        company,
        1 if data.get("include_images", True) else 0,
    )
    db = get_db()
    db.execute(
        """INSERT INTO profiles (id, industry, tone, platforms, brand_keywords, niche_keywords, goals, details, company, include_images)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET
              industry=excluded.industry,
              tone=excluded.tone,
              platforms=excluded.platforms,
              brand_keywords=excluded.brand_keywords,
              niche_keywords=excluded.niche_keywords,
              goals=excluded.goals,
              details=excluded.details,
              company=excluded.company,
              include_images=excluded.include_images
        """,
        row,
    )
    db.commit()
    return jsonify({"ok": True, "profile_id": profile_id})


@app.get("/api/profile")
def get_profile():
    profile_id = session.get("profile_id")
    uid = session.get('user_id')
    if not profile_id:
        return jsonify({})
    db = get_db()
    row = db.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
    if not row:
        return jsonify({})
    # parse stored JSON fields
    def parse_json_field(val, default=None):
        try:
            if not val:
                return [] if default is None else default
            return json.loads(val)
        except Exception:
            return [] if default is None else default

    details_obj = parse_json_field(row["details"], {})
    industry_key = None
    if isinstance(details_obj, dict):
        industry_key = details_obj.get("_industry_key") or details_obj.get("industry_key")
    return jsonify({
        "id": row["id"],
        "industry": row["industry"],
        "industry_key": industry_key,
        "tone": row["tone"],
        "platforms": parse_json_field(row["platforms"], []),
        "brand_keywords": parse_json_field(row["brand_keywords"], []),
        "niche_keywords": parse_json_field(row["niche_keywords"], []),
        "goals": parse_json_field(row["goals"], []),
        "details": details_obj,
        "company": row["company"] or "",
        "include_images": bool(row["include_images"]),
        "created_at": row["created_at"],
    })

@app.post("/api/generate")
def api_generate():
    uid = session.get('user_id')
    if not uid:
        return jsonify({'ok': False, 'error': 'Authentication required'}), 401

    db = get_db()
    user = db.execute('SELECT id, is_paid, free_sample_used FROM users WHERE id = ?', (uid,)).fetchone()
    if not user:
        return jsonify({'ok': False, 'error': 'Authentication required'}), 401

    data = request.get_json(force=True)
    profile_id = session.get("profile_id")
    days = int(data.get("days", 30))
    start_iso = data.get("start_date")
    try:
        start_day = date.fromisoformat(start_iso) if start_iso else date.today()
    except Exception:
        start_day = date.today()

    industry = data.get("industry", "Business")
    tone = data.get("tone", "friendly")
    platforms = data.get("platforms", ["instagram"])
    brand_keywords = data.get("brand_keywords", [])
    niche_keywords = data.get("niche_keywords", [])
    goals = data.get("goals", [])
    details = data.get("details", {})
    include_images = bool(data.get("include_images", True))
    company = data.get("company", "")
    details = data.get("details", {}) or {}

    reel_platforms = set(['tiktok', 'short_video'])
    requested_reel_platforms = [p for p in (platforms or []) if p and p.lower() in reel_platforms]
    reels_requested = max(0, len(requested_reel_platforms)) * int(days)
    is_paid = bool(user['is_paid'])
    free_sample_used = bool(user['free_sample_used'])
    is_reel_request = reels_requested > 0
    is_sample_request = days <= 1 and not is_reel_request
    consume_free_sample = False

    if not is_paid:
        if is_reel_request:
            return jsonify({'ok': False, 'error': 'Paid subscription required to generate reels'}), 403
        if days > 1:
            return jsonify({'ok': False, 'error': 'Paid subscription required to generate multi-day plans'}), 403
        if free_sample_used:
            return jsonify({'ok': False, 'error': 'You already used your free sample. Subscribe to unlock unlimited posts.'}), 403
        if not is_sample_request:
            return jsonify({'ok': False, 'error': 'Paid subscription required for this feature'}), 403
        consume_free_sample = True

    if is_reel_request:
        if not is_paid:
            return jsonify({'ok': False, 'error': 'Paid subscription required to generate reels'}), 403
        # Enforce monthly reel quota (prevents excessive generation). Tests expect this behavior.
        try:
            quota = int(os.getenv('REELS_QUOTA_MONTHLY', '30'))
        except Exception:
            quota = 30
        period = date.today().strftime('%Y-%m')
        row = db.execute('SELECT reels_generated FROM generation_usage WHERE user_id = ? AND period = ?', (uid, period)).fetchone()
        used = int(row['reels_generated']) if row and row['reels_generated'] is not None else 0
        if used + reels_requested > quota:
            return jsonify({'ok': False, 'error': 'Reel generation quota exceeded for this billing period', 'quota': quota, 'used': used}), 403

    posts = generate_posts_with_openai(
        days=days,
        start_day=start_day,
        industry=industry,
        tone=tone,
        platforms=platforms,
        brand_keywords=brand_keywords,
        include_images=include_images,
        niche_keywords=niche_keywords,
        goals=goals,
        details=details,
        company=company,
    )

    if not posts:
        posts = generator.generate_posts(
            days=days,
            start_day=start_day,
            industry=industry,
            tone=tone,
            platforms=platforms,
            brand_keywords=brand_keywords,
            include_images=include_images,
            niche_keywords=niche_keywords,
            goals=goals,
            details=details,
            company=company,
        )

    if consume_free_sample:
        try:
            db.execute('UPDATE users SET free_sample_used = 1 WHERE id = ?', (uid,))
            db.commit()
        except Exception:
            pass

    # if reels were requested, increment usage after successful generation
    if reels_requested > 0:
        try:
            period = date.today().strftime('%Y-%m')
            existing = db.execute('SELECT reels_generated FROM generation_usage WHERE user_id = ? AND period = ?', (uid, period)).fetchone()
            if existing:
                db.execute('UPDATE generation_usage SET reels_generated = reels_generated + ? WHERE user_id = ? AND period = ?', (reels_requested, uid, period))
            else:
                db.execute('INSERT INTO generation_usage (id, user_id, period, reels_generated) VALUES (?, ?, ?, ?)', (str(uuid.uuid4()), uid, period, reels_requested))
            db.commit()
        except Exception:
            # non-fatal: do not fail generation if usage increment fails
            pass
    return jsonify({"count": len(posts), "posts": posts, "profile_id": profile_id})

@app.post("/api/feedback")
def api_feedback():
    data = request.get_json(force=True)
    profile_id = session.get("profile_id")
    if not profile_id:
        return jsonify({"ok": False, "error": "No profile in session"}), 400
    db = get_db()
    db.execute(
        "INSERT INTO feedback (profile_id, post_day, platform, rating, note) VALUES (?, ?, ?, ?, ?)",
        (
            profile_id,
            int(data.get("post_day", 0)),
            data.get("platform"),
            int(data.get("rating", 0)),
            data.get("note", "")[:500],
        ),
    )
    db.commit()
    return jsonify({"ok": True})

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    # Run without the debugger/reloader here to avoid issues with the dev reloader
    # blocking incoming requests in some environments. For interactive debugging
    # set FLASK_DEBUG=1 and run with the flask CLI instead.
    app.run(host="0.0.0.0", port=port, debug=False)
