import pytest
from app import app as flask_app


@pytest.fixture(scope='session')
def app():
    # Provide the real Flask app for fixtures that need it.
    yield flask_app


@pytest.fixture(scope='session')
def live_server():
    """Return a small shim that provides live_server.url() pointing at the
    externally-running dev server used for e2e tests.

    This avoids pytest-flask starting a separate server instance (which was
    returning 404 for some routes in the test harness). Tests already use
    `page.goto(f'{live_server.url()}/...')` so returning this object is
    sufficient.
    """
    class _LS:
        def url(self):
            return "http://127.0.0.1:5001"

    return _LS()
