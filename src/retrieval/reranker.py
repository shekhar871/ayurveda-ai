from __future__ import annotations

import logging
from typing import Any

import httpx

from src.config import Settings

logger = logging.getLogger(__name__)


class Reranker:
    async def rerank(self, query: str, candidates: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        if not candidates:
            return []
        try:
            return await self._rerank_tei(query, candidates, top_k)
        except Exception as exc:
            logger.warning("TEI reranker unavailable (%s), using query-aware scores", exc)
            return sorted(
                candidates,
                key=lambda x: (
                    x.get("match_score", 0),
                    x.get("relevance", 0),
                    x.get("lexical_score", 0),
                    x.get("bm25_score", 0),
                ),
                reverse=True,
            )[:top_k]

    async def _rerank_tei(
        self, query: str, candidates: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        settings = Settings()
        texts = [c.get("text", "") for c in candidates]
        url = f"{settings.tei_url.rstrip('/')}/rerank"
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json={"query": query, "texts": texts, "truncate": True})
            resp.raise_for_status()
            ranked = resp.json()
        indices = [item["index"] for item in sorted(ranked, key=lambda x: x["score"], reverse=True)]
        out = []
        for idx in indices[:top_k]:
            item = dict(candidates[idx])
            item["rerank_score"] = next((r["score"] for r in ranked if r["index"] == idx), 0.0)
            out.append(item)
        return out
