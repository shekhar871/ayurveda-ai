from __future__ import annotations

import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router
from src.api.status import router as status_router
from src.config import get_settings
from src.services.bootstrap import init_services, shutdown_services

FRONTEND_DIST = Path(__file__).resolve().parents[1] / "frontend" / "dist"
# Docker mount path
if not (FRONTEND_DIST / "index.html").is_file():
    _docker_dist = Path("/app/frontend/dist")
    if (_docker_dist / "index.html").is_file():
        FRONTEND_DIST = _docker_dist

_rate_buckets: dict[str, list[float]] = defaultdict(list)

_SKIP_RATE_PREFIXES = ("/health", "/docs", "/openapi.json", "/assets", "/redoc", "/api/v1/status")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_services()
    yield
    await shutdown_services()


app = FastAPI(
    title="AyurVeda AI — OSS Core",
    version="1.0.0",
    description="Self-hosted 5-layer Ayurvedic intelligence engine",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    if path == "/" or any(path.startswith(p) for p in _SKIP_RATE_PREFIXES):
        return await call_next(request)

    settings = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    now = time.time()
    window = 60.0
    _rate_buckets[client_ip] = [t for t in _rate_buckets[client_ip] if now - t < window]

    if len(_rate_buckets[client_ip]) >= settings.rate_limit_per_minute:
        return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})

    _rate_buckets[client_ip].append(now)
    return await call_next(request)


@app.get("/health")
async def health():
    from src.services.bootstrap import _state

    mode = _state.mode if _state else "starting"
    return {
        "status": "ok",
        "service": "veda_ai_core",
        "mode": mode,
        "layers": ["ocr", "graph", "hybrid_retrieval", "llm_agents", "personalization"],
    }


app.include_router(router)
app.include_router(status_router)

if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/")
async def web_app():
    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)
    return JSONResponse(
        status_code=503,
        content={
            "detail": "Web UI not built. Run: cd frontend && npm install && npm run build",
            "api_docs": "/docs",
        },
    )


@app.get("/{page}")
async def spa_pages(page: str):
    """Support direct loads of client routes if added later."""
    if page.startswith("api") or page in ("docs", "openapi.json", "health", "redoc"):
        raise HTTPException(404)
    index = FRONTEND_DIST / "index.html"
    if index.is_file():
        return FileResponse(index)
    raise HTTPException(404)
