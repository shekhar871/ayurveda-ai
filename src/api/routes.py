from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException, Request

from src.agents.router import resolve_alternative_pathway
from src.api.schemas import (
    FeedbackRequest,
    IngestVerseRequest,
    ProfileRequest,
    ProgressFailureRequest,
    QueryRequest,
)
from src.ingestion.text_splitter import VerseEnvelope, chunk_to_envelopes
from src.services.bootstrap import get_state

router = APIRouter(prefix="/api/v1")


@router.post("/query")
async def query_endpoint(body: QueryRequest):
    state = get_state()
    started = time.perf_counter()
    result = await state.pipeline.run_query(
        query=body.query.strip(),
        user_id=body.user_id,
        season=body.season,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    return {
        "elapsed_ms": round(elapsed_ms, 2),
        "query": body.query.strip(),
        "result": result.model_dump(),
    }


@router.post("/profile")
async def upsert_profile(body: ProfileRequest):
    state = get_state()
    uid = await state.postgres.upsert_user_profile(
        body.user_id,
        {
            "prakriti": body.prakriti,
            "vikriti": body.vikriti,
            "allergies": body.allergies,
            "contraindications": body.contraindications,
            "active_protocol": body.active_protocol,
        },
    )
    return {"user_id": uid}


@router.post("/feedback")
async def record_feedback(body: FeedbackRequest):
    state = get_state()
    await state.postgres.record_feedback(
        body.user_id,
        body.formulation_name,
        body.outcome,
        body.checkpoint_day,
        body.notes,
    )
    delta = 0.2 if body.outcome == "helped" else -0.1 if body.outcome == "no_effect" else -0.3
    await state.postgres.boost_efficacy(body.user_id, body.formulation_name, delta)
    return {"status": "recorded", "efficacy_delta": delta}


@router.post("/progress/failure")
async def progress_failure(body: ProgressFailureRequest):
    state = get_state()
    started = time.perf_counter()
    result = await resolve_alternative_pathway(
        state.neo4j,
        state.postgres,
        body.user_id,
        body.current_protocol_id,
        body.observed_imbalance,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000
    if elapsed_ms > 500:
        result["warning"] = "fallback_exceeded_500ms_target"
    return {"elapsed_ms": round(elapsed_ms, 2), **result}


@router.post("/ingest/verse")
async def ingest_verse(body: IngestVerseRequest):
    state = get_state()
    envelopes = chunk_to_envelopes([body.model_dump()])
    env = envelopes[0]
    vec = (await state.embedder.embed_batch([env.text]))[0]
    vid = await state.postgres.upsert_verse(env, vec)
    state.qdrant.upsert_verse(env, vec)
    await state.postgres.register_citation(env.grantha, env.sthana, env.adhyaya, env.shloka)
    return {"verse_id": vid, "citation": env.citation_address()}


@router.post("/ingest/sample")
async def ingest_sample():
    import json
    from pathlib import Path

    corpus_path = Path(__file__).resolve().parents[2] / "data" / "corpus.json"
    SAMPLE_VERSES = json.loads(corpus_path.read_text(encoding="utf-8"))

    state = get_state()
    envelopes = chunk_to_envelopes(SAMPLE_VERSES)
    for env, rec in zip(envelopes, SAMPLE_VERSES):
        env.metadata = rec.get("metadata", {})
    texts = [e.text for e in envelopes]
    vectors = await state.embedder.embed_batch(texts)
    ids = []
    for env, vec in zip(envelopes, vectors):
        vid = await state.postgres.upsert_verse(env, vec)
        state.qdrant.upsert_verse(env, vec)
        await state.postgres.register_citation(env.grantha, env.sthana, env.adhyaya, env.shloka)
        ids.append(vid)
    state.retriever.invalidate_cache()
    await state.retriever.load_corpus_index()
    return {"ingested": len(ids), "verse_ids": ids}


@router.get("/retrieve")
async def retrieve_only(q: str, limit: int = 5):
    if len(q) < 3:
        raise HTTPException(400, "Query too short")
    state = get_state()
    hits = await state.retriever.retrieve(q, top_k=limit)
    return {"hits": hits}
