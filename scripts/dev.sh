#!/usr/bin/env bash
# Start the whole app locally: orchestrator API (:8001), upload API (:8002), frontend (:3000).
# Ctrl-C stops everything.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ ! -f "$ROOT/.env" ]]; then
  echo "Missing $ROOT/.env - copy .env.example and set ANTHROPIC_API_KEY." >&2
  exit 1
fi
set -a; source "$ROOT/.env"; set +a

# Stop the whole process group (uv, uvicorn and next spawn child processes)
cleanup() { trap - EXIT INT TERM; kill 0 2>/dev/null || true; }
trap cleanup EXIT INT TERM

(cd "$ROOT/backend/orchestrator-lambda" && uv run --extra local-rag uvicorn local_server:app --port 8001) &
(cd "$ROOT/backend/trigger-upload-lambda" && uv run --group local uvicorn local_server:app --port 8002) &
(cd "$ROOT/frontend" && npm run dev) &

echo "Frontend: http://localhost:3000  |  API: http://localhost:8001/docs  |  Upload: http://localhost:8002/docs"
wait
