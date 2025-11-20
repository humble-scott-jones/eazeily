#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: feedback_smoke.sh [--env FILE] [--base-url URL] [--start-local] [--python PYTHON]

Validates the feedback -> GitHub automation by:
  1. Sending a thumbs-down payload to /api/feedback
  2. Sending a settings feedback payload to /api/feedback/report

Options:
  --env FILE        Path to env file to source before running (default: .env.feedback-smoke)
  --base-url URL    Base URL to target (default: http://127.0.0.1:5001)
  --start-local     Start a local Flask server with the provided env before running requests
  --python PYTHON   Python executable to use when starting the server (default: python3)
  -h, --help        Show this help text
EOF
}

ENV_FILE=".env.feedback-smoke"
BASE_URL="http://127.0.0.1:5001"
START_LOCAL=0
PYTHON_BIN="python3"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env)
      ENV_FILE="$2"; shift 2 ;;
    --base-url)
      BASE_URL="$2"; shift 2 ;;
    --start-local)
      START_LOCAL=1; shift ;;
    --python)
      PYTHON_BIN="$2"; shift 2 ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1 ;;
  esac
done

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE" >&2
  echo "Create one with: cp .env.example $ENV_FILE" >&2
  exit 1
fi

TMP_ENV=$(mktemp)
trap 'rm -f "$TMP_ENV"' EXIT

# Filter comments and exportable KEY=VALUE lines into a temp file so `set -a` works reliably.
grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE" > "$TMP_ENV"
set -a
source "$TMP_ENV"
set +a

SERVER_PID=""
cleanup() {
  if [[ -n "$SERVER_PID" ]]; then
    kill "$SERVER_PID" >/dev/null 2>&1 || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

wait_for_server() {
  local url="$1"
  for attempt in $(seq 1 40); do
    if curl -sSf "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

if [[ "$START_LOCAL" -eq 1 ]]; then
  LOG_FILE=$(mktemp)
  echo "Starting local server with $PYTHON_BIN app.py (logs -> $LOG_FILE)"
  (set -a; source "$TMP_ENV"; set +a; "$PYTHON_BIN" app.py > "$LOG_FILE" 2>&1 &) 
  SERVER_PID=$!
  if ! wait_for_server "$BASE_URL/__dev__/ping"; then
    echo "Server failed to become ready. Tail of log:" >&2
    tail -n 100 "$LOG_FILE" >&2 || true
    exit 1
  fi
fi

post_json() {
  local endpoint="$1"
  local payload="$2"
  local label="$3"
  local http_output
  http_output=$(curl -sS -w "\n%{http_code}" -H 'Content-Type: application/json' -X POST -d "$payload" "$BASE_URL$endpoint")
  local body status
  body=$(echo "$http_output" | sed '$d')
  status=$(echo "$http_output" | tail -n1)
  if [[ "$status" != "200" ]]; then
    echo "[$label] Request failed ($status)" >&2
    echo "$body" >&2
    exit 1
  fi
  echo "$body"
}

now_iso=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
thumbs_payload=$(cat <<JSON
{
  "rating": -1,
  "post_day": 2,
  "platform": "instagram",
  "note": "Smoke test thumbs-down at $now_iso",
  "summary": "Smoke test: adjust Tuesday caption",
  "post_snapshot": "Day 2 caption sample for smoke test",
  "plan_length": 5,
  "source": "smoke-script"
}
JSON
)

general_payload=$(cat <<JSON
{
  "summary": "Smoke feedback $now_iso",
  "details": "Everything works but we want darker mode.",
  "category": "idea",
  "allow_contact": true,
  "platform": "instagram",
  "plan_length": 5,
  "source": "smoke-script"
}
JSON
)

thumbs_response=$(post_json "/api/feedback" "$thumbs_payload" "thumbs-down")
issue_url=$(python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('issue_url',''))" <<<"$thumbs_response")
if [[ -z "$issue_url" ]]; then
  echo "Thumbs-down feedback succeeded but no issue URL was returned. Ensure GitHub env vars are set." >&2
else
  echo "Thumbs-down issue created: $issue_url"
fi

report_response=$(post_json "/api/feedback/report" "$general_payload" "settings-feedback")
report_issue=$(python3 -c "import json,sys; data=json.load(sys.stdin); print(data.get('issue_url',''))" <<<"$report_response")
if [[ -n "$report_issue" ]]; then
  echo "Settings feedback issue created: $report_issue"
else
  echo "Settings feedback accepted (no GitHub issue when automation disabled)."
fi

echo "Feedback smoke test completed successfully."
