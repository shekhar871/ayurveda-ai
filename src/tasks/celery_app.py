from __future__ import annotations

from celery import Celery

from src.config import get_settings

settings = get_settings()

celery_app = Celery(
    "veda_workers",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
)


@celery_app.task(name="scrape_pubmed_stub")
def scrape_pubmed_stub(query: str) -> dict:
    """Placeholder for Phase 2 PubMed/CCRAS scrapers."""
    return {"query": query, "status": "queued", "source": "pubmed_stub"}


@celery_app.task(name="ingest_manuscript")
def ingest_manuscript_task(image_path: str, grantha: str, sthana: str, adhyaya: int, language: str = "san"):
    import asyncio

    from src.config import get_settings
    from src.database.postgres_client import PostgresClient
    from src.database.qdrant_client import QdrantStore
    from src.embeddings.tei_client import EmbeddingClient
    from src.ingestion.ocr_processor import process_manuscript_image

    async def _run():
        settings = get_settings()
        pg = PostgresClient(settings)
        qdrant = QdrantStore(settings)
        embedder = EmbeddingClient(settings)
        await pg.connect()
        await qdrant.ensure_collection()
        envelopes = await process_manuscript_image(image_path, grantha, sthana, adhyaya, language)
        vectors = await embedder.embed_batch([e.text for e in envelopes])
        for env, vec in zip(envelopes, vectors):
            await pg.upsert_verse(env, vec)
            qdrant.upsert_verse(env, vec)
        await pg.close()
        return len(envelopes)

    return asyncio.run(_run())
