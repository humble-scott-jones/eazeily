<!-- Please provide a short summary of the change and the motivation for it. -->

## Summary

Brief description of the changes in this PR.

## Changes


## Testing


## Notes

- High-level list of files and components modified (backend generator, dev endpoint, frontend dev UI, tests).

## How to test locally

- Unit tests: `pytest -q`
- Run only trend tests: `pytest tests/test_trends.py tests/test_trends_openai.py -q`
- Dev endpoint (dev-mode only): `/__dev__/trends?industry=restaurant` and `/__dev__/trends?industry=restaurant&force=1` (force is rate-limited)

## Environment / Config

- OPENAI_API_KEY — optional; when set the seeder can fetch fresh trends.
- TRENDS_TTL_HOURS — override cached TTL (default: 6)
- DEV_TRENDS_MIN_REFRESH_S — rate-limit for forced refresh in dev (default: 300)
- ALLOW_DEV_DEBUG or FLASK_ENV=development — enables dev endpoints and UI

## Reviewer checklist

- [ ] Unit tests pass locally and in CI
- [ ] New/changed code has adequate defensive checks (no unguarded model output assumptions)
- [ ] Cached trend files only contain validated items and are truncated to a small safe size
- [ ] Dev-only endpoints are gated and rate-limited
- [ ] No sensitive data is logged or persisted

## Deployment notes

- Change is backwards compatible. The trend seeder is opt-in for generation via `include_trends`.

## Follow-ups (optional)

- Add a JSON Schema validator for trend items.
- Add a Playwright e2e test to exercise the dev trends panel (dev-mode-only).

## Notes

Add any caveats, follow-ups, or implementation notes here.
