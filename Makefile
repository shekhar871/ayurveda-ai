.PHONY: run run-full run-lite up down logs test ingest seed health build prod

run:
	./run.sh

run-full:
	./run-full.sh

run-lite:
	./run-lite.sh

up:
	docker compose up -d postgres_oss qdrant_oss neo4j_oss redis_oss api worker

up-full:
	docker compose --profile full up -d

down:
	docker compose down

logs:
	docker compose logs -f api

build:
	docker compose build api worker

test:
	pytest tests/ -v

ingest:
	curl -s -X POST http://localhost:8000/api/v1/ingest/sample | python3 -m json.tool

seed:
	docker compose exec api python -m scripts.seed_sample_data

health:
	curl -s http://localhost:8000/health | python3 -m json.tool

query:
	curl -s -X POST http://localhost:8000/api/v1/query \
		-H "Content-Type: application/json" \
		-d '{"query":"Khalitya hair loss treatment","user_id":null}' | python3 -m json.tool

prod:
	docker compose --profile prod up -d
