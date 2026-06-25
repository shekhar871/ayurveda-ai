# AyurVeda AI

**Self-hosted Ayurvedic intelligence platform** with citation-verified RAG, knowledge-graph safety checks, and a production-grade 5-layer architecture — built for resume demos and real deployment.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-3776AB?logo=python&logoColor=white)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)]()
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)]()
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)]()
[![Tests](https://img.shields.io/badge/tests-14%20passing-brightgreen)]()

> Classical Ayurveda meets modern ML infrastructure: hybrid retrieval, Neo4j contraindications, and strict grounding gates — no hallucinated remedies.

**Live demo (local):** http://127.0.0.1:8000  
**API docs:** http://127.0.0.1:8000/docs

---

## Highlights (resume-ready)

| Capability | Implementation |
|------------|----------------|
| **Hybrid RAG** | Qdrant vectors + PostgreSQL FTS + BM25 + cross-encoder rerank |
| **Knowledge graph** | Neo4j formulation ↔ condition ↔ contraindication edges |
| **Grounding gate** | Query-intent analyzer + domain validator — zero fake hits |
| **Multi-agent pipeline** | Retrieval → citation audit → RAG compliance → answer builder |
| **Personalization** | JSONB profiles, feedback-driven efficacy scoring |
| **Full-stack UI** | React + Tailwind SPA served from FastAPI |

---

## Architecture

```
┌─────────────┐   ┌──────────────┐   ┌─────────────────┐   ┌──────────────┐   ┌────────────────┐
│  Layer 1    │   │   Layer 2    │   │    Layer 3      │   │   Layer 4    │   │    Layer 5     │
│  Ingestion  │ → │  Graph       │ → │  Hybrid RAG     │ → │  LLM Agents  │ → │ Personalization│
│  OCR/Chunk  │   │  Neo4j       │   │  Qdrant+FTS     │   │  vLLM+Guards │   │  Profiles      │
└─────────────┘   └──────────────┘   └─────────────────┘   └──────────────┘   └────────────────┘
```

**Tech stack:** Python · FastAPI · PostgreSQL (pgvector) · Qdrant · Neo4j · Redis · Celery · vLLM · BGE-M3 · React · Vite · Tailwind · Docker Compose

---

## Quick start

### Lite mode (no Docker — instant demo)

```bash
git clone https://github.com/shekhar871/ayurveda-ai.git
cd ayurveda-ai
./run-lite.sh
```

Open **http://127.0.0.1:8000** — searches run against a curated classical corpus with strict relevance validation.

### Full stack (production architecture)

Requires **Docker Desktop**:

```bash
./run-full.sh
```

Uses PostgreSQL + Qdrant + Neo4j + Redis. Health endpoint returns `"mode": "docker"`.

---

## Knowledge base

The indexed corpus pairs **Sanskrit ślokas** from classical granthas with English clinical glosses:

| Source | Content |
|--------|---------|
| Charaka Samhita | Sthoulya, Amlapitta, dosha dietetics |
| Ashtanga Hridayam | Khalitya, Darunaka, Pitta, Guggulu |
| Sushruta Samhita | Pitta qualities, Triphala |
| Bhaishajya Ratnavali | Kamadudha Rasa for Amlapitta |

See [DATA_SOURCES.md](./DATA_SOURCES.md) for provenance and citation format.

**Sample queries:** `weight loss`, `acidity remedies`, `Khalitya hair loss`, `Pitta contraindications`

---

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health + mode |
| GET | `/api/v1/status` | Stack layers + corpus stats |
| POST | `/api/v1/query` | Full RAG pipeline |
| POST | `/api/v1/profile` | Upsert Prakriti/Vikriti |
| POST | `/api/v1/feedback` | Efficacy feedback loop |
| POST | `/api/v1/progress/failure` | Neo4j alternative pathway |
| POST | `/api/v1/ingest/sample` | Re-index corpus |
| GET | `/api/v1/retrieve?q=` | Debug hybrid retrieval |

```bash
curl -X POST http://127.0.0.1:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "weight loss"}'
```

---

## Tests

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lite.txt pytest
PYTHONPATH=. pytest tests/ -q
./scripts/verify_api.sh
```

---

## Deploy

| Component | Platform | Guide |
|-----------|----------|-------|
| **Frontend** | Vercel | [DEPLOYMENT.md](./DEPLOYMENT.md) — set **Root Directory = `frontend`** |
| **API + DB** | Railway / Render / Fly.io | Docker Compose or Dockerfile |

---

## Project structure

```
veda_ai_core/
├── src/                 # FastAPI backend (5 layers)
├── frontend/            # React SPA (Vercel-ready)
├── data/corpus.json     # Classical knowledge base
├── docker-compose.yml   # Full OSS stack
├── run-lite.sh          # Local demo
├── run-full.sh          # Docker production stack
└── tests/               # Grounding + relevance tests
```

---

## Author

**Shekhar Jadhav** — built as a portfolio project demonstrating full-stack AI engineering with domain-specific RAG and graph safety.

## License

MIT — see [LICENSE](./LICENSE)

## Disclaimer

This system provides classical reference retrieval for educational purposes. It is **not** a substitute for licensed medical care. Always consult a qualified Ayurvedic physician (Vaidya).
