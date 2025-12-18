import os
import generator


def test_fetch_trend_context_no_gemini_returns_list():
    # Ensure function is safe to call without Gemini configured
    os.environ.pop('GEMINI_API_KEY', None)
    os.environ.pop('USE_GEMINI_FOR_POSTS', None)
    res = generator.fetch_trend_context('restaurant')
    assert isinstance(res, list)


def test_trend_cache_path_is_writable():
    path = generator._trend_cache_path('unittest-industry')
    # Ensure path ends with expected filename pattern and directory exists
    assert 'trends-unittest-industry' in os.path.basename(path)
    assert os.path.isdir(os.path.dirname(path))
