# staging/tests — CI & smoke tests

Purpose
- Harden CI, add smoke tests and ensure PR gating before merging into staging.

Commits to apply
- 009a5d4 (hardens /api/generate + acceptance smoke + secret scan)

Files of interest
- `.github/workflows/ci.yml`
- `tests/` (new smoke tests)

Steps
1. git checkout staging/tests
2. Cherry-pick commits or copy CI changes
3. Open PR and confirm CI runs pytest and smoke jobs

Verification
- [ ] CI runs and passes on PRs
- [ ] Smoke tests pass in staging after deploy
