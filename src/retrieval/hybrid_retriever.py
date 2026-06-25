from __future__ import annotations

from typing import Any

from rank_bm25 import BM25Okapi

from src.config import Settings
from src.embeddings.tei_client import EmbeddingClient
from src.retrieval.lexical_search import search_corpus
from src.retrieval.match_validator import filter_verified_hits
from src.retrieval.query_analyzer import QueryIntent, analyze_query
from src.retrieval.reranker import Reranker


class HybridRetriever:
    """Query-driven retrieval — ranking recomputed fresh on every search."""

    def __init__(
        self,
        settings: Settings,
        postgres: Any,
        qdrant: Any,
        neo4j: Any,
        embedder: EmbeddingClient,
    ) -> None:
        self._settings = settings
        self._pg = postgres
        self._qdrant = qdrant
        self._neo4j = neo4j
        self._embedder = embedder
        self._reranker = Reranker()
        self._corpus_cache: list[dict[str, Any]] | None = None
        self._bm25_index: BM25Okapi | None = None
        self._bm25_corpus: list[dict[str, Any]] = []

    def invalidate_cache(self) -> None:
        self._corpus_cache = None
        self._bm25_index = None
        self._bm25_corpus = []

    async def load_corpus_index(self) -> None:
        self.invalidate_cache()
        self._corpus_cache = await self._load_all_verse_texts()
        self._bm25_corpus = self._corpus_cache or []
        if self._bm25_corpus:
            tokenized = [self._doc_text(d).lower().split() for d in self._bm25_corpus]
            self._bm25_index = BM25Okapi(tokenized)

    def _doc_text(self, doc: dict) -> str:
        meta = doc.get("metadata") or {}
        topics = " ".join(str(t) for t in meta.get("topics", []))
        conds = " ".join(str(c) for c in meta.get("conditions", []))
        return f"{doc.get('text', '')} {topics} {conds}"

    async def _load_all_verse_texts(self) -> list[dict[str, Any]]:
        if hasattr(self._pg, "_data"):
            return [
                {
                    "text": v["text"],
                    "metadata": v.get("metadata", {}),
                    "grantha": v.get("grantha"),
                    "sthana": v.get("sthana"),
                    "adhyaya": v.get("adhyaya"),
                    "shloka": v.get("shloka"),
                    "language": v.get("language"),
                }
                for v in self._pg._data.get("verses", [])
            ]
        try:
            hits = await self._pg.fts_search("a", 200)
            return hits if hits else []
        except Exception:
            return []

    async def _get_corpus(self) -> list[dict[str, Any]]:
        if not self._corpus_cache:
            await self.load_corpus_index()
        return self._corpus_cache or []

    def _bm25_boost(self, query: str, docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self._bm25_index or not self._bm25_corpus:
            return docs
        tokens = query.lower().split()
        scores = self._bm25_index.get_scores(tokens)
        bm25_map: dict[str, float] = {}
        for i, s in enumerate(scores):
            if s > 0 and i < len(self._bm25_corpus):
                key = f"{self._bm25_corpus[i].get('grantha')}:{self._bm25_corpus[i].get('shloka')}:{i}"
                bm25_map[key] = float(s)
        for d in docs:
            key = f"{d.get('grantha')}:{d.get('shloka')}:{d.get('text', '')[:20]}"
            for i, c in enumerate(self._bm25_corpus):
                if c.get("text") == d.get("text"):
                    d["bm25_score"] = float(scores[i]) if scores[i] > 0 else 0.0
                    d["match_score"] = d.get("match_score", 0) + d["bm25_score"] * 0.15
                    break
        docs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return docs

    async def retrieve(
        self,
        query: str,
        user_profile: dict[str, Any] | None = None,
        top_k: int = 5,
        query_intent: QueryIntent | None = None,
    ) -> list[dict[str, Any]]:
        intent = query_intent or analyze_query(query)
        corpus = await self._get_corpus()

        if not corpus:
            return []

        # Primary: fresh per-query lexical + semantic scoring (NOT cached ranking)
        hits = search_corpus(query, corpus, intent=intent, top_k=top_k * 3, min_score=0.08)
        hits = self._bm25_boost(query, hits)

        if user_profile:
            efficacy = user_profile.get("efficacy_scores") or {}
            for item in hits:
                fname = (item.get("metadata") or {}).get("formulation")
                if fname and fname in efficacy:
                    item["match_score"] = item.get("match_score", 0) + float(efficacy[fname]) * 0.03

        hits.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        hits = hits[: top_k * 2]

        reranked = await self._reranker.rerank(query, hits, top_k=top_k)
        reranked = filter_verified_hits(query, intent, reranked)[:top_k]

        for item in reranked:
            herb = (item.get("metadata") or {}).get("dravya")
            if herb:
                try:
                    item["graph_attributes"] = await self._neo4j.get_formulation_attributes(herb)
                except Exception:
                    pass

        return reranked[:top_k]
