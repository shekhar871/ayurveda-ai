from __future__ import annotations

import logging

import httpx

from src.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """HuggingFace TEI when available; sentence-transformers fallback for dev."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._fallback_model = None

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            return await self._embed_tei(texts)
        except Exception as exc:
            logger.warning("TEI unavailable (%s), using local fallback", exc)
            return self._embed_local(texts)

    async def embed_query(self, text: str) -> list[float]:
        vectors = await self.embed_batch([text])
        return vectors[0]

    async def _embed_tei(self, texts: list[str]) -> list[list[float]]:
        url = f"{self._settings.tei_url.rstrip('/')}/embed"
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json={"inputs": texts})
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, list) and data and isinstance(data[0], list):
                return data
            if isinstance(data, dict) and "embeddings" in data:
                return data["embeddings"]
            raise ValueError("Unexpected TEI response format")

    def _embed_local(self, texts: list[str]) -> list[list[float]]:
        if self._settings.app_mode == "lite":
            from src.embeddings.hash_embedder import hash_embed_batch

            return hash_embed_batch(texts, dim=self._settings.embedding_dim)
        try:
            if self._fallback_model is None:
                from sentence_transformers import SentenceTransformer

                self._fallback_model = SentenceTransformer("BAAI/bge-m3")
            embeddings = self._fallback_model.encode(texts, normalize_embeddings=True)
            return [e.tolist() for e in embeddings]
        except Exception:
            from src.embeddings.hash_embedder import hash_embed_batch

            logger.warning("sentence-transformers unavailable, using hash embeddings")
            return hash_embed_batch(texts, dim=self._settings.embedding_dim)
