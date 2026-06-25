from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from src.agents.pipeline import AgentPipeline
from src.config import Settings, get_settings
from src.database.lite_backend import LiteBackend, LiteEmbedder, LiteQdrantAdapter
from src.embeddings.tei_client import EmbeddingClient
from src.llm.vllm_client import VLLMClient
from src.retrieval.hybrid_retriever import HybridRetriever

logger = logging.getLogger(__name__)


@dataclass
class AppState:
    settings: Settings
    postgres: Any
    qdrant: Any
    neo4j: Any
    embedder: Any
    retriever: HybridRetriever
    pipeline: AgentPipeline
    mode: str


_state: AppState | None = None


async def _seed_lite_if_empty(lite: LiteBackend) -> None:
    if lite._data.get("verses"):
        return
    import json
    from pathlib import Path

    from src.ingestion.text_splitter import chunk_to_envelopes

    corpus_path = Path(__file__).resolve().parents[2] / "data" / "corpus.json"
    if not corpus_path.is_file():
        logger.warning("corpus.json missing — lite store empty")
        return
    records = json.loads(corpus_path.read_text(encoding="utf-8"))
    embedder = LiteEmbedder()
    envelopes = chunk_to_envelopes(records)
    for env, rec in zip(envelopes, records):
        env.metadata = rec.get("metadata", {})
    vectors = await embedder.embed_batch([e.text for e in envelopes])
    for env, vec in zip(envelopes, vectors):
        await lite.upsert_verse(env, vec)
        await lite.register_citation(env.grantha, env.sthana, env.adhyaya, env.shloka)
    graph = {
        "Bhringraj Taila": {"indicated_in": ["Khalitya", "Darunaka"], "contraindicated_for": ["Pitta aggravation", "Amlapitta", "Acidity"], "trials": 1, "citations": 2},
        "Shatavari Swarasa": {"indicated_in": ["Amlapitta", "Acidity"], "contraindicated_for": [], "trials": 2, "citations": 2},
        "Amalaki Rasayana": {"indicated_in": ["Amlapitta", "Acidity"], "contraindicated_for": [], "trials": 2, "citations": 2},
        "Kamadudha Rasa": {"indicated_in": ["Amlapitta", "Acidity"], "contraindicated_for": [], "trials": 1, "citations": 1},
        "Guduchi Kashaya": {"indicated_in": ["Amlapitta", "Acidity"], "contraindicated_for": [], "trials": 1, "citations": 1},
        "Trikatu Churna": {"indicated_in": ["Kapha aggravation"], "contraindicated_for": ["Pitta aggravation", "Amlapitta", "Acidity"], "trials": 0, "citations": 1},
        "Malayaja Taila": {"indicated_in": ["Darunaka"], "contraindicated_for": [], "trials": 1, "citations": 1},
        "Yava Ahara": {"indicated_in": ["Sthoulya"], "contraindicated_for": [], "trials": 1, "citations": 1},
        "Guggulu Yoga": {"indicated_in": ["Sthoulya"], "contraindicated_for": [], "trials": 2, "citations": 2},
        "Triphala Kashaya": {"indicated_in": ["Sthoulya"], "contraindicated_for": [], "trials": 1, "citations": 1},
    }
    lite._data.setdefault("graph", {})["formulations"] = graph
    lite._save()
    logger.info("Seeded %d verses into lite store", len(envelopes))


async def _init_lite(settings: Settings) -> AppState:
    lite = LiteBackend()
    await lite.connect()
    await _seed_lite_if_empty(lite)
    await lite.ensure_collection()

    qdrant = LiteQdrantAdapter(lite)
    embedder = LiteEmbedder()
    retriever = HybridRetriever(settings, lite, qdrant, lite, embedder)
    await retriever.load_corpus_index()
    llm = VLLMClient(settings)
    pipeline = AgentPipeline(retriever, llm, lite, lite)

    return AppState(
        settings=settings,
        postgres=lite,
        qdrant=qdrant,
        neo4j=lite,
        embedder=embedder,
        retriever=retriever,
        pipeline=pipeline,
        mode="lite",
    )


@retry(stop=stop_after_attempt(12), wait=wait_exponential(multiplier=1, min=1, max=8))
async def _connect_full(postgres: Any, qdrant: Any, neo4j: Any) -> None:
    await postgres.connect()
    await qdrant.ensure_collection()
    await neo4j.connect()


async def _init_full(settings: Settings) -> AppState:
    from src.database.neo4j_client import Neo4jClient
    from src.database.postgres_client import PostgresClient
    from src.database.qdrant_client import QdrantStore

    postgres = PostgresClient(settings)
    qdrant = QdrantStore(settings)
    neo4j = Neo4jClient(settings)
    embedder = EmbeddingClient(settings)

    await _connect_full(postgres, qdrant, neo4j)

    retriever = HybridRetriever(settings, postgres, qdrant, neo4j, embedder)
    await retriever.load_corpus_index()
    llm = VLLMClient(settings)
    pipeline = AgentPipeline(retriever, llm, postgres, neo4j)

    return AppState(
        settings=settings,
        postgres=postgres,
        qdrant=qdrant,
        neo4j=neo4j,
        embedder=embedder,
        retriever=retriever,
        pipeline=pipeline,
        mode="docker",
    )


async def init_services() -> AppState:
    global _state
    if _state:
        return _state

    settings = get_settings()
    mode = settings.app_mode.lower()

    if mode == "lite":
        _state = await _init_lite(settings)
        logger.info("Started in LITE mode (no Docker required)")
        return _state

    if mode == "docker":
        try:
            _state = await _init_full(settings)
            logger.info("Started in DOCKER mode (full stack)")
            return _state
        except Exception as exc:
            logger.warning("Docker stack unavailable (%s), falling back to lite", exc)
            _state = await _init_lite(settings)
            return _state

    # auto: try docker, fallback lite
    try:
        _state = await _init_full(settings)
        logger.info("Started in AUTO→docker mode")
        return _state
    except Exception as exc:
        logger.warning("AUTO mode: full stack failed (%s), using lite", exc)
        _state = await _init_lite(settings)
        return _state


async def shutdown_services() -> None:
    global _state
    if not _state:
        return
    await _state.postgres.close()
    if _state.mode == "docker":
        await _state.neo4j.close()
    _state = None


def get_state() -> AppState:
    if not _state:
        raise RuntimeError("Services not initialized")
    return _state
