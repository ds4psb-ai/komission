#!/usr/bin/env bash
# Smoke test for coaching session + WebSocket handshake.
# Usage: scripts/smoke_coaching_ws.sh
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
VENV_PY="${BACKEND_DIR}/venv/bin/python"
VENV_UVICORN="${BACKEND_DIR}/venv/bin/uvicorn"

PYTHON_BIN="${VENV_PY}"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="$(command -v python3 || command -v python)"
fi

if [[ -x "${VENV_UVICORN}" ]]; then
  UVICORN_CMD=("${VENV_UVICORN}")
else
  UVICORN_CMD=("${PYTHON_BIN}" -m uvicorn)
fi

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8001}"
SKIP_GEMINI_LIVE="${SKIP_GEMINI_LIVE:-1}"
LOG_FILE="${TMPDIR:-/tmp}/komission_uvicorn_${PORT}.log"
SESSION_JSON="${TMPDIR:-/tmp}/komission_session_${PORT}.json"
WS_RESULT="${TMPDIR:-/tmp}/komission_ws_result_${PORT}.json"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python not found. Install Python 3 and dependencies." >&2
  exit 1
fi

if [[ "${#UVICORN_CMD[@]}" -eq 0 ]]; then
  echo "uvicorn not found. Install backend dependencies." >&2
  exit 1
fi

GEMINI_API_KEY="${GEMINI_API_KEY:-local_dummy}" \
SKIP_GEMINI_LIVE="${SKIP_GEMINI_LIVE}" \
  "${UVICORN_CMD[@]}" app.main:app \
  --app-dir "${BACKEND_DIR}" \
  --host "${HOST}" \
  --port "${PORT}" \
  --log-level warning \
  >"${LOG_FILE}" 2>&1 &
PID=$!

cleanup() {
  kill "${PID}" >/dev/null 2>&1 || true
  wait "${PID}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for _ in {1..30}; do
  if curl -fsS "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if ! curl -fsS "http://${HOST}:${PORT}/health" >/dev/null 2>&1; then
  echo "health_check_failed"
  tail -n 200 "${LOG_FILE}"
  exit 1
fi

if ! "${PYTHON_BIN}" - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("websockets") else 1)
PY
then
  echo "websockets module not found. Install backend deps (pip install -r backend/requirements.txt)." >&2
  exit 1
fi

curl -fsS -X POST "http://${HOST}:${PORT}/api/v1/coaching/sessions" \
  -H "Content-Type: application/json" \
  -d '{}' \
  >"${SESSION_JSON}"

HOST="${HOST}" PORT="${PORT}" SESSION_JSON="${SESSION_JSON}" WS_RESULT="${WS_RESULT}" \
  "${PYTHON_BIN}" - <<'PY'
import asyncio
import json
import os
from pathlib import Path

import websockets

host = os.environ.get("HOST", "127.0.0.1")
port = os.environ.get("PORT", "8001")
session_path = Path(os.environ["SESSION_JSON"])
result_path = Path(os.environ["WS_RESULT"])

resp = json.loads(session_path.read_text())
session_id = resp.get("session_id")
if not session_id:
    raise SystemExit("missing session_id")

ws_url = f"ws://{host}:{port}/api/v1/ws/coaching/{session_id}?output_mode=graphic&persona=calm_mentor"

async def main() -> None:
    async with websockets.connect(ws_url, ping_interval=None) as ws:
        msg = await asyncio.wait_for(ws.recv(), timeout=5)
        connected = json.loads(msg)

        await ws.send(json.dumps({"type": "control", "action": "start"}))

        recording = None
        for _ in range(5):
            msg = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(msg)
            if data.get("type") == "session_status" and data.get("status") == "recording":
                recording = data
                break
        if connected.get("session_id") != session_id:
            raise SystemExit("connected_session_id_mismatch")
        if not recording:
            raise SystemExit("recording_status_missing")
        required_keys = [
            "type",
            "status",
            "gemini_connected",
            "fallback_mode",
            "coaching_tier",
            "effective_tier",
            "tier_downgraded",
        ]
        missing = [key for key in required_keys if key not in recording]
        if missing:
            raise SystemExit(f"recording_missing_keys:{','.join(missing)}")

        out = {
            "ws_url": ws_url,
            "connected_type": connected.get("type"),
            "connected_session_id": connected.get("session_id"),
            "recording_status": (recording or {}).get("status"),
            "gemini_connected": (recording or {}).get("gemini_connected"),
            "fallback_mode": (recording or {}).get("fallback_mode"),
        }
        result_path.write_text(json.dumps(out))
        print(json.dumps(out))

asyncio.run(main())
PY
