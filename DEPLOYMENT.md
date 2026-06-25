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

> **Important:** Vercel hosts the **React UI only**. Do NOT deploy the Python backend on Vercel — it exceeds the 500 MB serverless limit.

The repo includes a root `vercel.json` that builds **only** `frontend/` (static files).

### Vercel Dashboard settings (required)

1. Import: `github.com/shekhar871/ayurveda-ai`
2. **Root Directory:** leave **empty** (repo root `.`) — do NOT set to `frontend`
3. **Settings → Build & Development:** turn **OFF** all overrides (Install Command, Build Command, Output Directory) so `vercel.json` at repo root is used
4. Expected commands (from `vercel.json`):
   - Install: `npm ci --prefix frontend`
   - Build: `npm run build --prefix frontend`
   - Output: `frontend/dist`
5. After API deploy (step 2), add environment variable:
   - `VITE_API_URL` = `https://your-api.onrender.com` (no trailing slash)
6. Redeploy

> **Common mistake:** an old `.vercelignore` used `src/` which deleted `frontend/src/` from the upload. Fixed — patterns are now root-anchored (`/src/`).

### Option A — Vercel CLI

```bash
cd frontend
npm install
npm run build

# Set your backend URL (Render/Railway after step 2)
vercel env add VITE_API_URL production
# Example: https://ayurveda-ai-api.onrender.com

vercel --prod
```

### Option B — Vercel Dashboard

Push to `main` — connected GitHub repo auto-deploys when `vercel.json` is present.

`frontend/vercel.json` handles SPA routing.

---

## 2. Deploy backend API (Render — free tier)

The API **cannot** run on Vercel. Use Render with the included `Dockerfile.lite`:

1. Go to [render.com](https://render.com) → **New** → **Blueprint**
2. Connect repo `shekhar871/ayurveda-ai`
3. Render reads `render.yaml` and deploys `ayurveda-ai-api`
4. Copy the URL (e.g. `https://ayurveda-ai-api.onrender.com`)
5. In Vercel → Settings → Environment Variables → set `VITE_API_URL` to that URL
6. Redeploy Vercel frontend

**Or manual Render deploy:**
- New Web Service → Docker → `Dockerfile.lite`
- Env: `APP_MODE=lite`, `EMBEDDING_DIM=384`, `PYTHONPATH=.`

---

## 2b. Deploy backend (Railway alternative)

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
