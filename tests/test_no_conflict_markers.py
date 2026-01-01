import os
import re

# CI guard: fail if merge conflict markers appear in repository text files.
# Detects lines that are exact merge markers used by git: seven < or >, and seven = signs.

CONFLICT_PATTERNS = [
    re.compile(r"^\s*<{7}(\s.*)?$"),  # <<<<<<< or <<<<<<< HEAD
    re.compile(r"^\s*>{7}(\s.*)?$"),  # >>>>>>> or >>>>>>> stash
    re.compile(r"^\s*={7}\s*$"),      # ======= (exactly 7 equals)
]

EXCLUDED_DIRS = {'.git', '.venv', '__pycache__', 'node_modules', 'venv', 'dist', 'build'}


def is_text_file(path):
    # Try to read a small portion to guess if it's text
    try:
        with open(path, 'rb') as f:
            chunk = f.read(4096)
            # If NUL byte present, treat as binary
            if b"\x00" in chunk:
                return False
            return True
    except Exception:
        return False


def test_no_merge_conflict_markers():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    problems = []
    for dirpath, dirnames, filenames in os.walk(root):
        # prune excluded directories
        parts = set(dirpath.split(os.sep))
        if parts & EXCLUDED_DIRS:
            continue
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            # skip large typical artifacts
            if any(p in path for p in ('/.git/', '/.venv/', '/node_modules/', '/venv/', '/dist/', '/build/')):
                continue
            if not is_text_file(path):
                continue
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    for i, line in enumerate(f, start=1):
                        for pat in CONFLICT_PATTERNS:
                            if pat.match(line):
                                problems.append(f"{path}:{i}: {line.strip()}")
            except Exception:
                # If we can't read, skip the file
                continue

    if problems:
        msg = "Found merge conflict markers in repository:\n" + "\n".join(problems)
        raise AssertionError(msg)
