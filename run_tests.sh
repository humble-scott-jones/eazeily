#!/usr/bin/env bash
set -euo pipefail

# Always use the repo's virtualenv interpreter to keep versions consistent
VENV_PY=".venv/bin/python"
if [ ! -x "$VENV_PY" ]; then
	echo ".venv is missing. Create it with: python3 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt"
	exit 1
fi

"$VENV_PY" -m pip install -r requirements.txt

# By default run unit tests only. To run UI smoke tests set RUN_UI_SMOKE=1
if [ -n "${RUN_UI_SMOKE:-}" ]; then
	echo "Running UI smoke tests (RUN_UI_SMOKE=${RUN_UI_SMOKE})"
	PYTHONPATH=. "$VENV_PY" -m pytest -q -m ui "$@"
else
	PYTHONPATH=. "$VENV_PY" -m pytest -q "$@"
fi
