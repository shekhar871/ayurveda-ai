#!/usr/bin/env bash
# Launch AyurVeda AI Web App (full stack if Docker available)
cd "$(dirname "$0")"
if docker info &>/dev/null 2>&1; then
  exec ./run-full.sh
else
  echo "Docker not running → lite web app (./run-full.sh or ./start-webapp.sh for full stack)"
  exec ./run-lite.sh
fi
