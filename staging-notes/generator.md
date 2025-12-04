# staging/generator — Content generation improvements

Purpose
- Restore reel/platform hints, caption improvements, and generator unit tests.

Commits to apply
- 342513f, fa13542, b17f233, bad833e, 9f10201, 67259f6

Files of interest
- `generator.py`
- `tests/test_generator_unit.py`
- `tests/test_generator_reel.py`

Steps
1. git checkout staging/generator
2. Cherry-pick the generator commits or copy modified files into the branch.
3. Run tests:
   - PYTHONPATH=. pytest tests/test_generator_unit.py tests/test_generator_reel.py -q
4. Deploy to staging and run an API generate sample to confirm payloads.

Verification
- [ ] Generator unit tests pass
- [ ] API generate endpoint returns valid payloads
