# Togetherly - GitHub Copilot Instructions

## Architecture & Core Patterns
- **Framework**: Flask (Python 3.10+) with SQLite (`togetherly.db`) and Vanilla JS frontend.
- **Service Boundaries**:
  - `app.py`: Routes, auth, DB management, and business logic orchestration.
  - `generator.py`: Pure logic for content generation (posts, captions, hashtags). Decoupled from Flask context where possible.
  - `static/content/config.json`: **Source of Truth** for industry definitions, tones, and pillars. Edit this to add/modify business types.
  - `static/content/flags.json`: Client-side feature flags.
- **Database Access**:
  - Use `get_db()` context manager pattern (implied in `app.py`).
  - Prefer `sqlite3.Row` for dictionary-like access.
  - **Constraint**: SQLite is the only DB. No ORM (raw SQL with parameterized queries).

## Development Workflow
- **Environment**: Always activate venv: `source .venv/bin/activate`.
- **Run Server**: `PORT=5001 python3 app.py` (Default port 5001).
- **Dependencies**: Managed in `requirements.txt`. Optional deps (Stripe, OpenAI) are handled with try/except blocks in `app.py`.

## Testing Strategy
- **Runner**: `pytest`.
- **Command**: `PYTHONPATH=. pytest -q` or use `./run_tests.sh`.
- **UI Smoke Tests**: Gated by env var. Run with `RUN_UI_SMOKE=1 PYTHONPATH=. pytest -q`.
- **Fixtures**: Defined in `tests/conftest.py`. Each test gets an isolated temporary SQLite DB.
- **Best Practice**: When adding features, add a corresponding test file in `tests/` following the `test_*.py` pattern.

## Project Specifics
- **Frontend**: NO frameworks (React/Vue). Use standard DOM API (`document.querySelector`, `fetch`).
- **Content Generation**:
  - Logic resides in `generator.py`.
  - Uses `PLATFORM_HINTS` and `PILLARS_BY_DEFAULT` constants.
  - OpenAI integration is optional; code must handle missing API keys gracefully.
- **Configuration**:
  - To add an industry: Update `static/content/config.json` (add to `industries` array and `questions` object).
  - To toggle features: Update `static/content/flags.json`.

## Common Tasks
- **New Route**: Add to `app.py`, ensure `@login_required` if needed.
- **New Industry**: Edit `static/content/config.json`.
- **Database Schema**: Update `init_db()` in `app.py` (no migration tool currently active, handle schema changes carefully).

