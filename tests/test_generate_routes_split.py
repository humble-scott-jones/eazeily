"""Tests to ensure generation pages are split per route."""


def test_social_page_renders_with_marker(client):
    response = client.get('/generate/social')

    assert response.status_code == 200
    html = response.data.decode('utf-8')

    assert 'data-page-id="social"' in html
    assert 'data-endpoint-marker="/api/generate"' in html


def test_reels_page_renders_with_marker(client):
    response = client.get('/generate/reels')

    assert response.status_code == 200
    html = response.data.decode('utf-8')

    assert 'data-page-id="reels"' in html
    assert 'data-endpoint-marker="/api/generate"' in html


def test_reviews_page_renders_with_marker(client):
    response = client.get('/generate/reviews')

    assert response.status_code == 200
    html = response.data.decode('utf-8')

    assert 'data-page-id="reviews"' in html
    assert 'data-endpoint-marker="/api/generate-review-response"' in html
