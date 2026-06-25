#!/usr/bin/env bash
# Full original stack: PostgreSQL + Qdrant + Neo4j + Redis + Web UI
set -euo pipefail
cd "$(dirname "$0")"

if ! docker info &>/dev/null 2>&1; then
  echo ""
  echo "ERROR: Docker Desktop is not running."
  echo ""
  echo "  1. Open Docker Desktop and wait until it says 'Running'"
  echo "  2. Run this script again:  ./run-full.sh"
  echo ""
  echo "  For a quick demo without Docker, use:  ./run-lite.sh"
  echo ""
  exit 1
fi

echo "==> Using FULL stack (docker mode)"
cp .env.full .env

echo "==> Starting databases (Postgres, Qdrant, Neo4j, Redis)..."
docker compose up -d postgres_oss qdrant_oss neo4j_oss redis_oss

echo "==> Waiting for services to become healthy (Neo4j may take ~90s)..."
docker compose up -d --wait postgres_oss qdrant_oss redis_oss 2>/dev/null || true

for i in $(seq 1 60); do
  if docker compose exec -T neo4j_oss neo4j status 2>/dev/null | grep -q "running\|Running"; then
    echo "    Neo4j is ready."
    break
  fi
  if [[ $i -eq 60 ]]; then
    echo "    Neo4j still starting — continuing anyway..."
  fi
  sleep 3
done

if [[ ! -d .venv ]]; then
  if command -v python3.11 &>/dev/null; then
    python3.11 -m venv .venv
  else
    python3 -m venv .venv
  fi
fi
source .venv/bin/activate

echo "==> Installing full Python dependencies (first run may take a few minutes)..."
pip install -q -r requirements.txt

export PYTHONPATH=.
set -a && source .env && set +a

echo "==> Seeding verses into Postgres + Qdrant + Neo4j graph..."
python3 scripts/seed_corpus.py full

if command -v npm &>/dev/null; then
  echo "==> Building web UI..."
  cd frontend
  [[ -d node_modules ]] || npm install --silent
  npm run build --silent
  cd ..
fi

echo ""
echo "=============================================="
echo "  AyurVeda AI Web Application (FULL STACK)"
echo ""
echo "  >>> Open in browser:  http://127.0.0.1:8000"
echo ""
echo "  Neo4j:  http://127.0.0.1:7474"
echo "  Qdrant: http://127.0.0.1:6333/dashboard"
echo "=============================================="
echo ""

PORT=8000
if lsof -ti:"$PORT" &>/dev/null; then
  echo "Stopping previous server on port $PORT..."
  lsof -ti:"$PORT" | xargs kill -9 2>/dev/null || true
  sleep 1
fi

exec python3 -m uvicorn src.main:app --host 127.0.0.1 --port "$PORT" --reload
