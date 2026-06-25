#!/usr/bin/env bash
# Everything inside Docker (API + worker + databases)
set -euo pipefail
cd "$(dirname "$0")"

if ! docker info &>/dev/null 2>&1; then
  echo "Start Docker Desktop first."
  exit 1
fi

if command -v npm &>/dev/null; then
  echo "Building web UI..."
  cd frontend && npm install --silent && npm run build --silent && cd ..
fi

cp .env.full .env
docker compose build api worker
docker compose up -d postgres_oss qdrant_oss neo4j_oss redis_oss

echo "Waiting for databases..."
sleep 30
docker compose up -d api worker

echo "Seeding data..."
docker compose exec -T api python scripts/seed_sample_data.py || true

echo ""
echo "  Web app:  http://127.0.0.1:8000"
echo "  Neo4j:    http://127.0.0.1:7474  (neo4j / neo4j_local_secret)"
echo ""
