"""Verify each generation page exposes the endpoint marker used by the UI."""

import pytest


@pytest.mark.parametrize(
    "path, marker",
    [
        ("/generate/social", "/api/generate/social"),
        ("/generate/reels", "/api/generate/social"),
        ("/generate/reviews", "/api/generate-review-response"),
    ],
)
def test_page_has_endpoint_marker(client, path, marker):
    response = client.get(path)

    assert response.status_code == 200
    html = response.data.decode('utf-8')

    assert marker in html
