#!/usr/bin/env python3
"""Seed sample data for lite mode (no Docker)."""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config import get_settings
from src.database.lite_backend import LiteBackend, LiteEmbedder
from src.ingestion.text_splitter import chunk_to_envelopes

SAMPLE_PATH = Path(__file__).resolve().parents[1] / "data" / "sample_verses.json"


async def main() -> None:
    settings = get_settings()
    settings.app_mode = "lite"
    lite = LiteBackend()
    embedder = LiteEmbedder()
    verses = json.loads(SAMPLE_PATH.read_text(encoding="utf-8"))
    envelopes = chunk_to_envelopes(verses)
    vectors = await embedder.embed_batch([e.text for e in envelopes])

    for env, vec in zip(envelopes, vectors):
        await lite.upsert_verse(env, vec)
        await lite.register_citation(env.grantha, env.sthana, env.adhyaya, env.shloka)

    lite._data["verses"][-1]["metadata"] = {"formulation": "Bhringraj Taila", "dravya": "Bhringraj"}
    lite._save()
    print(f"Lite store seeded: {len(envelopes)} verses at {lite._path}")


if __name__ == "__main__":
    asyncio.run(main())
