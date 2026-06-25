#!/usr/bin/env python3
"""Seed sample verses and graph nodes for local development."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import get_settings
from src.database.postgres_client import PostgresClient
from src.database.qdrant_client import QdrantStore
from src.database.neo4j_client import Neo4jClient
from src.embeddings.tei_client import EmbeddingClient
from src.ingestion.text_splitter import VerseEnvelope, chunk_to_envelopes
from src.graph.builder import GraphBuilder

import json
from pathlib import Path

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_verses.json"
SAMPLE_VERSES = json.loads(SAMPLE_PATH.read_text())


async def main() -> None:
    settings = get_settings()
    pg = PostgresClient(settings)
    qdrant = QdrantStore(settings)
    neo4j = Neo4jClient(settings)
    embedder = EmbeddingClient(settings)
    graph = GraphBuilder(neo4j)

    await pg.connect()
    await qdrant.ensure_collection()
    await neo4j.connect()

    envelopes = chunk_to_envelopes(SAMPLE_VERSES)
    texts = [e.text for e in envelopes]
    vectors = await embedder.embed_batch(texts)

    for env, vec in zip(envelopes, vectors):
        if "Bhringraj" in env.text or "bhringraj" in env.text.lower():
            env.metadata["formulation"] = "Bhringraj Taila"
            env.metadata["dravya"] = "Bhringraj"
        await pg.upsert_verse(env, vec)
        qdrant.upsert_verse(env, vec)
        await pg.register_citation(env.grantha, env.sthana, env.adhyaya, env.shloka)

    await graph.seed_sample_graph()
    print(f"Seeded {len(envelopes)} verses and graph sample nodes.")
    await pg.close()
    await neo4j.close()


if __name__ == "__main__":
    asyncio.run(main())
