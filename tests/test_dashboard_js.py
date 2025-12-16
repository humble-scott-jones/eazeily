import shutil
import subprocess
from pathlib import Path

import pytest


def test_dashboard_js_parses():
    node = shutil.which("node")
    if not node:
        pytest.skip("node not available")

    result = subprocess.run(
        [node, "--check", str(Path("static/dashboard.js"))],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"dashboard.js has syntax errors: {result.stderr or result.stdout}"


def test_publishing_queue_state_declared():
    """Verify publishingQueueState access pattern is declared in code"""
    dashboard_js_path = Path("static/dashboard.js")
    content = dashboard_js_path.read_text()
    
    # Check for publishingQueueState reference (now via getter or namespaced)
    assert "publishingQueueState" in content, "publishingQueueState should be referenced"
    
    # Check for either the getter function or the legacy alias
    has_getter = "function getPublishingQueueState()" in content
    has_legacy_alias = "const publishingQueueState =" in content or "let publishingQueueState =" in content
    
    assert has_getter or has_legacy_alias, \
        "Should have either getPublishingQueueState() function or publishingQueueState alias"
    
    # Check for PUBLISHING_QUEUE_STORAGE_KEY declaration
    assert "PUBLISHING_QUEUE_STORAGE_KEY" in content, "PUBLISHING_QUEUE_STORAGE_KEY should be declared"
    assert "const PUBLISHING_QUEUE_STORAGE_KEY" in content or "let PUBLISHING_QUEUE_STORAGE_KEY" in content or "var PUBLISHING_QUEUE_STORAGE_KEY" in content, \
        "PUBLISHING_QUEUE_STORAGE_KEY should be declared as a constant"
    
    # Check that entries property is referenced
    assert "entries" in content, "Queue state should have entries property referenced"


def test_queue_functions_have_defensive_checks():
    """Verify queue functions include defensive null checks"""
    dashboard_js_path = Path("static/dashboard.js")
    content = dashboard_js_path.read_text()
    
    # Check that critical functions have defensive checks
    # Now they should use getPublishingQueueState() or check queueState
    has_getter_check = "getPublishingQueueState()" in content
    has_direct_check = "if (!publishingQueueState" in content or "if (!queueState" in content
    
    assert has_getter_check or has_direct_check, \
        "Functions should check queue state via getter or direct check"
    
    # Check that findQueueEntry has a defensive check
    find_queue_entry_start = content.find("function findQueueEntry(")
    if find_queue_entry_start > 0:
        find_queue_entry_section = content[find_queue_entry_start:find_queue_entry_start + 300]
        has_check = (
            "getPublishingQueueState()" in find_queue_entry_section or
            "if (!queueState" in find_queue_entry_section or
            "if (!publishingQueueState" in find_queue_entry_section
        )
        assert has_check, "findQueueEntry should have defensive checks"


