# staging/voice-profile — Voice profile onboarding & guardrails

Purpose
- Add voice profile onboarding, validation, and batching improvements.

Commits to apply
- dbffb0b, 97d7b9b, a8c39c7

Files of interest
- `voice_profile.py`
- `app.py` (routes)
- `static/dashboard.js`

Steps
1. git checkout staging/voice-profile
2. Cherry-pick or copy the commits
3. Run voice profile tests:
   - PYTHONPATH=. pytest tests/test_voice_profile.py -q
4. Test onboarding flow in staging UI.

Verification
- [ ] Voice profile tests pass
- [ ] Onboarding UI completes and creates profile entries
