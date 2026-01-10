"""Legacy GenerationService contract suite skipped after Gemini migration."""

import pytest

pytestmark = pytest.mark.skip(
    reason="Legacy GenerationService social/reel/review helpers removed; skipping contract suite",
)


def test_generation_service_contract_placeholder():
    """Placeholder to keep collection succeeding while suite is skipped."""
    assert True
