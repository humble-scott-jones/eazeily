"""Root conftest.py to configure pytest collection for the entire project."""
import os

# Skip scripts folder test files - these are standalone diagnostic scripts,
# not part of the regular test suite
collect_ignore = [
    'scripts',
    'archive',
]
