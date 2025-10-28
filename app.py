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

Commit message: "Enable OpenAI-backed generation for /api/generate; fallback to local generator"
