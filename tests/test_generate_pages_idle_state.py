import re


PATHS = ["/generate/social", "/generate/reviews"]


def _has_hidden_overlay(html: str) -> bool:
    return bool(re.search(r'data-loading-overlay[^>]+class="[^"]*hidden', html))


def _has_hidden_banner(html: str) -> bool:
    return bool(re.search(r'data-error-banner[^>]+class="[^"]*hidden', html))


def test_generate_pages_start_idle(client):
    for path in PATHS:
        resp = client.get(path)
        assert resp.status_code == 200
        html = resp.data.decode()
        assert 'data-async-state="idle"' in html
        assert _has_hidden_overlay(html)
        assert _has_hidden_banner(html)
