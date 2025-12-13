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
