Title: feat(trends): LLM-only trend seeder, caching, validation, dev endpoint, and tests

Summary

This PR adds an LLM-driven trend seeder that produces lightweight topical signals (topic + rationale + confidence) for a given industry without relying on external social APIs. The seeder is conservative and local-only: it validates model output, caches only validated results, and is opt-in for generation flows.

Why

- Makes generated posts more topical by optionally including recent trend context in prompts.
- Keeps the codebase and CI deterministic by providing an LLM-only seeder (no scraping or external API calls besides the configured LLM).
- Provides safe dev tooling to inspect and force-refresh cached trend context while rate-limiting force-refresh to avoid accidental mass requests.

High-level changes

- generator.fetch_trend_context(industry, locale="global", ttl_hours=None)
  - LLM-only trend seeder with robust parsing and normalization.
  - Caches validated results to `static/content/trends-{slug}.json` (TTL default 6 hours, configurable via TRENDS_TTL_HOURS).
  - Returns a list of up to 6 validated items: {topic, rationale, confidence}

- app.py
  - `generate_posts_with_openai(..., include_trends: bool = False)` now fetches `trend_context` (only when include_trends=True) and adds it to the payload sent to the model.
  - Dev endpoint `/__dev__/trends` to view cached trends and optionally force a refresh (dev-only, rate-limited by `DEV_TRENDS_MIN_REFRESH_S`).

- Frontend
  - Small Dev Trends panel on the homepage (visible in dev mode) that can load cached trends or force-refresh them.
  - `static/app.js` handlers to call `/__dev__/trends`.

- Tests
  - `tests/test_trends.py` — safe call when OpenAI disabled.
  - `tests/test_trends_openai.py` — mocks OpenAI shapes, asserts parsing and caching.

Files changed (representative)

- generator.py (new: fetch_trend_context + helpers + robustness)
- app.py (include_trends wiring + /__dev__/trends)
- templates/index.html (dev panel)
- static/app.js (UI handlers)
- tests/test_trends.py
- tests/test_trends_openai.py

How to test locally

1) Unit tests (fast)

- Run the unit test suite (recommended in a venv):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

- Run only trend tests:

```bash
pytest tests/test_trends.py tests/test_trends_openai.py -q
```

2) Manual dev flow (dev-mode only)

- Set dev-mode flags so the dev endpoint/UI is available.

```bash
export FLASK_ENV=development
# or
export ALLOW_DEV_DEBUG=1
```

- If you want to fetch fresh trends from the configured OpenAI client, ensure `OPENAI_API_KEY` is set. Otherwise the seeder returns [] and the dev endpoint shows cached (or empty) data.

- Open the app locally (default port 5000) and use the Dev Trends panel on the homepage to load cached trends or force-refresh (force refresh is rate-limited).

Curl examples (dev-mode):

```bash
# load cached
curl -s "http://localhost:5000/__dev__/trends?industry=restaurant" | jq

# force refresh (dev-only, may be rate-limited)
curl -s "http://localhost:5000/__dev__/trends?industry=restaurant&force=1" | jq
```

Environment variables (not exhaustive)

- OPENAI_API_KEY — if set, the trend seeder can fetch fresh trends.
- USE_OPENAI_FOR_POSTS — optional flag to gate live generation (project already uses OPENAI_API_KEY to set USE_OPENAI)
- TRENDS_TTL_HOURS — override TTL (default 6)
- DEV_TRENDS_MIN_REFRESH_S — min seconds between force refreshes for a given industry (dev only; default 300)
- ALLOW_DEV_DEBUG or FLASK_ENV=development — make dev endpoints/UI available

Review checklist

- [ ] Confirm no sensitive keys are logged or written to disk.
- [ ] Confirm cached trends are only stored when validated and truncated to a small safe size.
- [ ] Run unit tests locally and verify `tests/test_trends*` pass.
- [ ] Verify the dev panel can read the cached file and that force refresh is rate-limited.
- [ ] Validate that generation with `include_trends=true` includes a `trend_context` field in the payload sent to the model (backend unit/integration test or manual inspection).
- [ ] CI green (unit + Playwright e2e)

Notes / follow-ups

- We may want to add a JSON Schema validator for trend items to be stricter (low-risk follow-up).
- Optional: Add a Playwright e2e test to exercise the dev trends panel (dev-mode-only) and assert the UI shows cached content and handles rate-limiting.

Suggested reviewers

- @team-lead or whoever owns backend generation and tests.

---

(If you'd like I can open the PR on GitHub and paste this body for you, but that requires a GitHub token or using the GitHub UI.)
