# Rollout Plan: Staging to Production (2025-12-04)

This document outlines the incremental rollout plan to restore features and fix production issues.
Base Branch: `staging/rollout-2025-12-04` (Derived from `origin/integration/2025-11-sync`)

## 1. Database & Runtime Fixes (`staging/db-fix`)
**Goal:** Fix the application crash caused by Railway's `timeout` parameter in `DATABASE_URL`.
**Key Changes:**
- `app.py`: Update `_connect_db` to replace `?timeout=` with `?connect_timeout=` for `psycopg` v3 compatibility.
- `app.py`: Fix `NameError` in Postgres wrapper.
**Commits to Cherry-Pick:**
- `eb55b3a` (Fix DB connection: map timeout to connect_timeout)
- `1fc4ed0` (Robust fix for DB timeout param)
- `a9b508d` (Fix NameError in Postgres wrapper)

## 2. Dependencies & Environment (`staging/deps`)
**Goal:** Ensure production environment has all required packages and correct Docker image.
**Key Changes:**
- `requirements.txt`: Add `gunicorn`, `psycopg`, `SQLAlchemy`, `alembic`.
- `Dockerfile`: Restore `python:3.11-slim` (revert from Alpine if needed).
**Commits to Cherry-Pick:**
- `0bb33a5` (Add missing production dependencies)
- `91dfe32` (Restore Python Dockerfile)

## 3. Branding Update (`staging/branding`)
**Goal:** Update branding from "Swelly" to "Eazeily".
**Key Changes:**
- `templates/landing.html`: Update text and title.
- `static/eazeily-logo.svg`: Add new logo.
**Commits to Cherry-Pick:**
- `a6e1662` (Fix DB connection timeout issue and update branding to Eazeily)
  *Note: This commit contains both DB fix and branding. Verify if it needs splitting.*

## 4. Content Generator Features (`staging/generator`)
**Goal:** Restore recent improvements to content generation (Reels, captions).
**Key Changes:**
- `generator.py`: Reel platform hints, caption logic improvements.
- `tests/`: Updated generator tests.
**Commits to Cherry-Pick:**
- `342513f`, `fa13542`, `b17f233`, `bad833e`, `9f10201`, `67259f6`

## 5. Voice Profile & Onboarding (`staging/voice-profile`)
**Goal:** Enable voice profile creation, onboarding flow, and guardrails.
**Key Changes:**
- `voice_profile.py`: Validation logic, embedding batching.
- `app.py`: Voice profile routes.
- `static/dashboard.js`: Onboarding UI.
**Commits to Cherry-Pick:**
- `dbffb0b`, `97d7b9b`, `a8c39c7`

## 6. Dashboard & Team Features (`staging/dashboard`)
**Goal:** Restore activity feed, team approvals, and dashboard UI updates.
**Key Changes:**
- `static/dashboard.js`: Activity feed, ownership tags.
- `templates/dashboard.html`: UI updates.
- `app.py`: Team routing logic.
**Commits to Cherry-Pick:**
- `4aeac0c`, `a3a0252`, `bfa25e2`, `20ffde8`

## 7. Publishing & Scheduling (`staging/publishing`)
**Goal:** Enable publishing queue and scheduling features.
**Key Changes:**
- `app.py`: Publishing logic.
- `static/dashboard.js`: Queue UI.
**Commits to Cherry-Pick:**
- `715c8a5`, `ac289f8`

## 8. Tests & CI (`staging/tests`)
**Goal:** Harden CI/CD and add smoke tests.
**Key Changes:**
- `.github/workflows/ci.yml`: CI updates.
- `tests/`: New smoke tests.
**Commits to Cherry-Pick:**
- `009a5d4`

---

## Database Setup & Migration Note
**Concern:** "Setting up postgres database and replacing it with old db"

**Current Status:**
- The application is configured to use `DATABASE_URL` from the environment.
- On Railway, this points to a managed Postgres instance.
- The code uses `psycopg` (v3) to connect.

**Migration/Setup Steps:**
1. **Schema Creation:** The app seems to use `init_db()` in `app.py` or Alembic migrations.
   - Check `alembic/` folder for migration scripts.
   - If `init_db()` is used, it might try to create tables on startup.
2. **Data Migration:**
   - If you have an "old db" (SQLite `togetherly.db` or another Postgres dump), you need to import it to the new Railway Postgres instance.
   - **Action:** Use `pg_dump` (from old) and `psql` (to new) or a data migration script.
   - If moving from SQLite: You'll need a tool like `pgloader` or a custom script to move data from `togetherly.db` to Postgres.

**Verification:**
- Once `staging/db-fix` is deployed, check logs to see if tables are found.
- If tables are missing, run `alembic upgrade head` (if using Alembic) or trigger `init_db()`.
