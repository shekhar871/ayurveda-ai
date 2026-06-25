from __future__ import annotations

import hashlib
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from src.config import Settings
from src.ingestion.text_splitter import VerseEnvelope


def _point_id(envelope: VerseEnvelope) -> str:
    key = f"{envelope.grantha}:{envelope.sthana}:{envelope.adhyaya}:{envelope.shloka}:{envelope.language}"
    return hashlib.md5(key.encode()).hexdigest()


class QdrantStore:
    def __init__(self, settings: Settings) -> None:
        self._client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        self._collection = settings.qdrant_collection
        self._dim = settings.embedding_dim

    async def ensure_collection(self) -> None:
        collections = [c.name for c in self._client.get_collections().collections]
        if self._collection not in collections:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=qm.VectorParams(size=self._dim, distance=qm.Distance.COSINE),
            )

    def upsert_verse(self, envelope: VerseEnvelope, embedding: list[float]) -> None:
        self._client.upsert(
            collection_name=self._collection,
            points=[
                qm.PointStruct(
                    id=_point_id(envelope),
                    vector=embedding,
                    payload={
                        "text": envelope.text,
                        "grantha": envelope.grantha,
                        "sthana": envelope.sthana,
                        "adhyaya": envelope.adhyaya,
                        "shloka": envelope.shloka,
                        "language": envelope.language,
                        "metadata": envelope.metadata,
                    },
                )
            ],
        )

    def dense_search(self, query_vector: list[float], limit: int = 10) -> list[dict[str, Any]]:
        hits = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=limit,
            with_payload=True,
        )
        results = []
        for hit in hits:
            p = hit.payload or {}
            results.append(
                {
                    "score": hit.score,
                    "text": p.get("text", ""),
                    "grantha": p.get("grantha"),
                    "sthana": p.get("sthana"),
                    "adhyaya": p.get("adhyaya"),
                    "shloka": p.get("shloka"),
                    "language": p.get("language"),
                    "metadata": p.get("metadata", {}),
                }
            )
        return results
