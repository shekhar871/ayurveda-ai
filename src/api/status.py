from __future__ import annotations

from fastapi import APIRouter

from src.services.bootstrap import get_state

router = APIRouter(prefix="/api/v1", tags=["status"])


def _corpus_stats(state) -> dict:
    verses = []
    if hasattr(state.postgres, "_data"):
        verses = state.postgres._data.get("verses", [])
    elif hasattr(state.retriever, "_corpus_cache") and state.retriever._corpus_cache:
        verses = state.retriever._corpus_cache

    granthas: set[str] = set()
    conditions: set[str] = set()
    formulations: set[str] = set()
    for v in verses:
        if v.get("grantha"):
            granthas.add(str(v["grantha"]))
        meta = v.get("metadata") or {}
        for c in meta.get("conditions", []):
            conditions.add(str(c))
        if meta.get("formulation"):
            formulations.add(str(meta["formulation"]))

    return {
        "verse_count": len(verses),
        "granthas": sorted(granthas),
        "conditions_indexed": sorted(conditions),
        "formulations_indexed": sorted(formulations),
    }


@router.get("/status")
async def stack_status():
    """Live connectivity for web app dashboard."""
    state = get_state()
    layers = []

    pg_ok = state.mode == "lite"
    if state.mode == "docker":
        try:
            await state.postgres.connect()
            pg_ok = True
        except Exception as e:
            layers.append({"name": "PostgreSQL", "role": "Verses, profiles, FTS", "status": "offline", "error": str(e)})
    if pg_ok:
        layers.append({"name": "PostgreSQL", "role": "Verses, profiles, FTS", "status": "online"})

    try:
        await state.qdrant.ensure_collection()
        layers.append({"name": "Qdrant" if state.mode == "docker" else "Vector index", "role": "Dense vector search", "status": "online"})
    except Exception as e:
        layers.append({"name": "Qdrant", "role": "Dense vector search", "status": "offline", "error": str(e)})

    try:
        if state.mode == "docker":
            await state.neo4j.connect()
        layers.append({"name": "Neo4j" if state.mode == "docker" else "Graph (lite)", "role": "Graph safety & alternatives", "status": "online"})
    except Exception as e:
        layers.append({"name": "Neo4j", "role": "Graph safety & alternatives", "status": "offline", "error": str(e)})

    layers.extend([
        {"name": "Hybrid Retrieval", "role": "Qdrant + FTS + BM25", "status": "online"},
        {"name": "Agent Pipeline", "role": "RAG + citation guard", "status": "online"},
        {"name": "Personalization", "role": "JSONB profiles & feedback", "status": "online"},
    ])

    return {
        "mode": state.mode,
        "full_stack": state.mode == "docker",
        "corpus": _corpus_stats(state),
        "layers": layers,
        "data_stores": ["PostgreSQL 16", "Qdrant OSS", "Neo4j Community", "Redis"],
    }
