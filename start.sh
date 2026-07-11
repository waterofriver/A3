#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/Course-Agent/creative"
LOGS="$ROOT/artifacts/logs"
PYTHON="$BACKEND/.venv/bin/python"
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-3000}"

mkdir -p "$LOGS"
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/.env"
  set +a
fi
if [[ ! -x "$PYTHON" ]]; then
  python3 -m venv "$BACKEND/.venv"
fi

"$PYTHON" -m pip install -e "$BACKEND[test]"
corepack pnpm --dir "$FRONTEND" install --frozen-lockfile
(cd "$BACKEND" && "$PYTHON" -m alembic upgrade head)

export NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:$API_PORT"
export NEXT_PUBLIC_AGENT_MODE="${NEXT_PUBLIC_AGENT_MODE:-${AGENT_MODE:-mock}}"

"$PYTHON" -m uvicorn app.main:app --app-dir "$BACKEND" --host 127.0.0.1 --port "$API_PORT" --workers 1 >"$LOGS/api.log" 2>"$LOGS/api-error.log" &
API_PID=$!
corepack pnpm --dir "$FRONTEND" dev --hostname 127.0.0.1 --port "$WEB_PORT" >"$LOGS/web.log" 2>"$LOGS/web-error.log" &
WEB_PID=$!

trap 'kill "$API_PID" "$WEB_PID" 2>/dev/null || true' EXIT INT TERM
echo "Web: http://127.0.0.1:$WEB_PORT"
echo "API: http://127.0.0.1:$API_PORT/docs"
echo "PIDs: api=$API_PID, web=$WEB_PID"
wait "$API_PID" "$WEB_PID"
