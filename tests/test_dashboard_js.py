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
    """Verify publishingQueueState and PUBLISHING_QUEUE_STORAGE_KEY are declared in code"""
    dashboard_js_path = Path("static/dashboard.js")
    content = dashboard_js_path.read_text()
    
    # Check for publishingQueueState declaration
    assert "publishingQueueState" in content, "publishingQueueState should be declared"
    assert "const publishingQueueState = {" in content or "let publishingQueueState = {" in content or "var publishingQueueState = {" in content, \
        "publishingQueueState should be initialized as an object"
    
    # Check for PUBLISHING_QUEUE_STORAGE_KEY declaration
    assert "PUBLISHING_QUEUE_STORAGE_KEY" in content, "PUBLISHING_QUEUE_STORAGE_KEY should be declared"
    assert "const PUBLISHING_QUEUE_STORAGE_KEY" in content or "let PUBLISHING_QUEUE_STORAGE_KEY" in content or "var PUBLISHING_QUEUE_STORAGE_KEY" in content, \
        "PUBLISHING_QUEUE_STORAGE_KEY should be declared as a constant"
    
    # Check that publishingQueueState has entries property initialized
    assert "entries:" in content, "publishingQueueState should have entries property"


def test_queue_functions_have_defensive_checks():
    """Verify queue functions include defensive null checks"""
    dashboard_js_path = Path("static/dashboard.js")
    content = dashboard_js_path.read_text()
    
    # Check that critical functions have defensive checks
    assert "if (!publishingQueueState" in content, "Functions should check if publishingQueueState exists"
    
    # Check that findQueueEntry has a defensive check
    find_queue_entry_start = content.find("function findQueueEntry(")
    if find_queue_entry_start > 0:
        find_queue_entry_section = content[find_queue_entry_start:find_queue_entry_start + 300]
        assert "if (!publishingQueueState" in find_queue_entry_section or "publishingQueueState?" in find_queue_entry_section, \
            "findQueueEntry should have defensive checks"


