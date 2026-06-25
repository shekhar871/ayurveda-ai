#!/usr/bin/env bash
# Lite demo — no Docker (file-backed storage)
set -euo pipefail
cd "$(dirname "$0")"

export APP_MODE=lite
export EMBEDDING_DIM=384
cp .env.example .env 2>/dev/null || true
echo "APP_MODE=lite" > .env
echo "EMBEDDING_DIM=384" >> .env

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install -q -r requirements-lite.txt
python3 scripts/seed_corpus.py lite

if command -v npm &>/dev/null; then
  cd frontend && [[ -d node_modules ]] || npm install --silent
  npm run build --silent && cd ..
fi

PORT=8000
if lsof -ti:"$PORT" &>/dev/null; then
  echo "Stopping previous server on port $PORT..."
  lsof -ti:"$PORT" | xargs kill -9 2>/dev/null || true
  sleep 1
fi

echo ""
echo "=============================================="
echo "  AyurVeda AI Web App (lite mode)"
echo "  Open: http://127.0.0.1:$PORT"
echo "=============================================="
echo ""

exec python3 -m uvicorn src.main:app --host 127.0.0.1 --port "$PORT" --reload
