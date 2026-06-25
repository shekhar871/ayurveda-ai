#!/usr/bin/env python3
"""Seed full corpus into Postgres+Qdrant+Neo4j or lite store."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

CORPUS = Path(__file__).resolve().parents[1] / "data" / "corpus.json"


async def seed_full() -> None:
    from src.config import get_settings
    from src.database.neo4j_client import Neo4jClient
    from src.database.postgres_client import PostgresClient
    from src.database.qdrant_client import QdrantStore
    from src.embeddings.tei_client import EmbeddingClient
    from src.graph.builder import GraphBuilder
    from src.ingestion.text_splitter import chunk_to_envelopes

    settings = get_settings()
    pg = PostgresClient(settings)
    qdrant = QdrantStore(settings)
    neo4j = Neo4jClient(settings)
    embedder = EmbeddingClient(settings)
    graph = GraphBuilder(neo4j)

    await pg.connect()
    await qdrant.ensure_collection()
    await neo4j.connect()

    records = json.loads(CORPUS.read_text(encoding="utf-8"))
    envelopes = chunk_to_envelopes(records)
    for env, rec in zip(envelopes, records):
        env.metadata = rec.get("metadata", {})

    vectors = await embedder.embed_batch([e.text for e in envelopes])
    for env, vec in zip(envelopes, vectors):
        await pg.upsert_verse(env, vec)
        qdrant.upsert_verse(env, vec)
        await pg.register_citation(env.grantha, env.sthana, env.adhyaya, env.shloka)

    await graph.seed_full_graph()
    print(f"Full stack: seeded {len(envelopes)} corpus entries.")
    await pg.close()
    await neo4j.close()


async def seed_lite_store() -> None:
    from src.database.lite_backend import LiteBackend, LiteEmbedder
    from src.ingestion.text_splitter import chunk_to_envelopes

    records = json.loads(CORPUS.read_text(encoding="utf-8"))
    lite = LiteBackend()
    lite._data = {"verses": [], "citations": [], "profiles": {}, "feedback": [], "graph": {"formulations": {}}}
    embedder = LiteEmbedder()
    envelopes = chunk_to_envelopes(records)
    for env, rec in zip(envelopes, records):
        env.metadata = rec.get("metadata", {})
    vectors = await embedder.embed_batch([e.text for e in envelopes])
    for env, vec in zip(envelopes, vectors):
        await lite.upsert_verse(env, vec)
        await lite.register_citation(env.grantha, env.sthana, env.adhyaya, env.shloka)

    lite._data["graph"]["formulations"] = {
        "Bhringraj Taila": {
            "indicated_in": ["Khalitya", "Darunaka"],
            "contraindicated_for": ["Pitta aggravation", "Amlapitta", "Acidity"],
            "trials": 1,
            "citations": 2,
        },
        "Shatavari Swarasa": {"indicated_in": ["Amlapitta", "Acidity"], "contraindicated_for": [], "trials": 2, "citations": 2},
        "Amalaki Rasayana": {"indicated_in": ["Amlapitta", "Acidity"], "contraindicated_for": [], "trials": 2, "citations": 2},
        "Kamadudha Rasa": {"indicated_in": ["Amlapitta", "Acidity"], "contraindicated_for": [], "trials": 1, "citations": 1},
        "Guduchi Kashaya": {"indicated_in": ["Amlapitta", "Acidity"], "contraindicated_for": [], "trials": 1, "citations": 1},
        "Trikatu Churna": {
            "indicated_in": ["Kapha aggravation"],
            "contraindicated_for": ["Pitta aggravation", "Amlapitta", "Acidity"],
            "trials": 0,
            "citations": 1,
        },
        "Malayaja Taila": {"indicated_in": ["Darunaka"], "contraindicated_for": [], "trials": 1, "citations": 1},
        "Yava Ahara": {"indicated_in": ["Sthoulya"], "contraindicated_for": [], "trials": 1, "citations": 1},
        "Guggulu Yoga": {"indicated_in": ["Sthoulya"], "contraindicated_for": [], "trials": 2, "citations": 2},
        "Triphala Kashaya": {"indicated_in": ["Sthoulya"], "contraindicated_for": [], "trials": 1, "citations": 1},
    }
    lite._save()
    print(f"Lite store: seeded {len(envelopes)} corpus entries → {lite._path}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "lite"
    if mode == "full":
        asyncio.run(seed_full())
    else:
        asyncio.run(seed_lite_store())
