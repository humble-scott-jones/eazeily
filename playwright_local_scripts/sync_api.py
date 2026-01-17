from __future__ import annotations
from contextlib import contextmanager

@contextmanager
def sync_playwright():
    # Minimal stub for tests that are skipped unless RUN_UI_SMOKE=1
    class _Browser:
        def close(self):
            return None
    class _Context:
        def close(self):
            return None
    class _Playwright:
        def __init__(self):
            self.chromium = self
        def launch(self, *args, **kwargs):
            return _Browser()
    pw = _Playwright()
    yield pw

# simple alias for expect used in some tests
class expect:
    def __init__(self, *args, **kwargs):
        pass
