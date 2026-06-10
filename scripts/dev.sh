#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$ROOT"
source .venv/bin/activate
python -m weaver.api &
API_PID=$!

cd "$ROOT/client"
npm run dev &
CLIENT_PID=$!

trap 'kill $API_PID $CLIENT_PID 2>/dev/null || true' EXIT
wait
