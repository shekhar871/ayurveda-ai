from __future__ import annotations

import math
import re
from typing import Any

from src.embeddings.hash_embedder import hash_embed
from src.retrieval.match_validator import document_matches_query, filter_verified_hits
from src.retrieval.query_analyzer import QueryIntent, analyze_query, is_negation_only_match, relevance_score

STOPWORDS = {"the", "and", "for", "with", "what", "how", "when", "about", "from", "this", "that", "are", "is"}


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z\u0900-\u097F]{2,}", text.lower()) if t not in STOPWORDS]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


def score_document(query: str, intent: QueryIntent, doc: dict[str, Any]) -> float:
    if not document_matches_query(query, intent, doc):
        return 0.0

    text = (doc.get("text") or "").lower()
    meta = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
    q_tokens = _tokens(query)
    blob = " ".join(
        [text]
        + [str(t) for t in meta.get("topics", [])]
        + [str(c) for c in meta.get("conditions", [])]
    ).lower()

    if intent.wants_remedy and is_negation_only_match(query, text):
        return 0.0

    blob_tokens = set(_tokens(blob))
    overlap = len(set(q_tokens) & blob_tokens) / max(len(q_tokens), 1)
    score = overlap * 0.55

    if query.lower() in text:
        score += 0.2

    score += _cosine(hash_embed(query), hash_embed(text)) * 0.15
    score += relevance_score(intent, doc) * 0.3

    content_type = str(meta.get("content_type", "")).lower()
    if intent.wants_remedy and content_type == "indication":
        score += 0.2

    return score


def search_corpus(
    query: str,
    corpus: list[dict[str, Any]],
    intent: QueryIntent | None = None,
    top_k: int = 6,
    min_score: float = 0.25,
) -> list[dict[str, Any]]:
    intent = intent or analyze_query(query)
    if not corpus:
        return []

    scored: list[dict[str, Any]] = []
    for doc in corpus:
        s = score_document(query, intent, doc)
        if s >= min_score:
            entry = {**doc, "lexical_score": s, "relevance": relevance_score(intent, doc)}
            entry["match_score"] = round(s * 0.65 + entry["relevance"] * 0.35, 4)
            scored.append(entry)

    scored.sort(key=lambda x: x["match_score"], reverse=True)
    verified = filter_verified_hits(query, intent, scored)
    return verified[:top_k]
