# Deployment Guide

## Overview

AyurVeda AI has two deployable parts:

| Part | Runtime | Recommended platform |
|------|---------|-------------------|
| **Frontend** (React SPA) | Static + env var | **Vercel** |
| **Backend** (FastAPI + DB) | Python + Docker | **Railway**, Render, or Fly.io |

The full PostgreSQL + Qdrant + Neo4j stack **cannot** run on Vercel serverless alone. Deploy the API separately and point the frontend at it.

---

## 1. Deploy frontend to Vercel

### Option A — Vercel CLI

```bash
cd frontend
npm install
npm run build

# Set your backend URL (Railway/Render after step 2)
vercel env add VITE_API_URL production
# Example: https://ayurveda-api.up.railway.app

vercel --prod
```

### Option B — Vercel Dashboard

1. Import repo: `shekhar871/ayurveda-ai`
2. Set **Root Directory** → `frontend`
3. Framework: **Vite**
4. Environment variable:
   - `VITE_API_URL` = `https://your-api-host.com` (no trailing slash)
5. Deploy

`frontend/vercel.json` handles SPA routing.

---

## 2. Deploy backend (Railway example)

```bash
# From repo root — uses Dockerfile
railway init
railway add --service api
railway up
```

Set environment variables on Railway:

```
APP_MODE=docker
POSTGRES_HOST=...
QDRANT_HOST=...
NEO4J_URI=...
REDIS_URL=...
```

Or use **lite mode** for a minimal demo API (no external DB):

```
APP_MODE=lite
EMBEDDING_DIM=384
```

Railway will expose a URL like `https://ayurveda-api.up.railway.app`. Set that as `VITE_API_URL` on Vercel.

### CORS

FastAPI already allows all origins in development. For production, restrict `allow_origins` in `src/main.py` to your Vercel domain.

---

## 3. Full Docker stack (VPS / cloud VM)

```bash
docker compose up -d postgres_oss qdrant_oss neo4j_oss redis_oss
docker compose build api && docker compose up -d api
```

With Nginx gateway:

```bash
docker compose --profile prod up -d
```

---

## 4. Verify deployment

```bash
curl https://your-api/health
curl -X POST https://your-api/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "acidity remedies"}'
```

---

## Resume / portfolio tip

List on your resume:

> **AyurVeda AI** — Self-hosted RAG platform (FastAPI, PostgreSQL, Qdrant, Neo4j, React). Citation-verified Ayurvedic retrieval with graph-based contraindication screening. [GitHub](https://github.com/shekhar871/ayurveda-ai) · [Live Demo](https://your-vercel-url.vercel.app)
