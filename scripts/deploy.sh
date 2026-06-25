#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example — update secrets before production."
fi

docker compose up -d postgres_oss qdrant_oss neo4j_oss redis_oss
docker compose build api worker
docker compose up -d api worker

echo "Waiting for API health..."
for i in {1..30}; do
  if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

curl -sf -X POST http://localhost:8000/api/v1/ingest/sample | python3 -m json.tool
echo "Deployment ready. API: http://localhost:8000/docs"
