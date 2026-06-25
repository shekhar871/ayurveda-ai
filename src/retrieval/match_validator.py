from __future__ import annotations

import re
from typing import Any

from src.retrieval.query_analyzer import QueryIntent, is_negation_only_match

# Tokens that alone cause false cross-domain matches (e.g. "loss" in hair loss vs weight loss)
AMBIGUOUS_TOKENS = frozenset({
    "loss", "pain", "help", "remedy", "remedies", "treatment", "cure", "problem",
    "condition", "disease", "disorder", "symptom", "symptoms", "issue", "issues",
})

MIN_MATCH_SCORE = 0.38
MIN_LEXICAL_FOR_UNKNOWN = 0.45


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z\u0900-\u097F]{2,}", text.lower())]


def document_matches_query(query: str, intent: QueryIntent, doc: dict[str, Any]) -> bool:
    """Strict gate — prevents hair-loss verses matching weight-loss queries."""
    text = (doc.get("text") or "").lower()
    meta = doc.get("metadata") if isinstance(doc.get("metadata"), dict) else {}
    meta_topics = [str(t).lower() for t in meta.get("topics", [])]
    meta_conditions = [str(c).lower() for c in meta.get("conditions", [])]
    blob = " ".join([text] + meta_topics + meta_conditions)

    if intent.wants_remedy and is_negation_only_match(query, text):
        return False

    # Known Ayurvedic condition in metadata must match detected conditions
    if intent.conditions:
        for cond in intent.conditions:
            c = cond.lower()
            if c in blob or c in meta_conditions or c.replace(" ", "") in blob.replace(" ", ""):
                if intent.is_contraindication or meta.get("content_type") != "indication":
                    if intent.wants_remedy and meta.get("content_type") == "contraindication":
                        return False
                    return True
        # Condition was requested but doc doesn't mention it
        if not intent.is_contraindication:
            topic_hit = any(
                t.replace("_", " ") in blob or t in meta_topics
                for t in intent.topics
            )
            if not topic_hit:
                return False

    q_tokens = _tokens(query)
    specific = [t for t in q_tokens if t not in AMBIGUOUS_TOKENS]

    if specific:
        blob_set = set(_tokens(blob))
        if not all(t in blob_set for t in specific):
            return False
    elif intent.conditions:
        return any(c.lower() in blob for c in intent.conditions)
    else:
        overlap = len(set(q_tokens) & set(_tokens(blob)))
        if overlap < max(1, len(q_tokens) * 0.6):
            return False

    # Block cross-domain: query has 'weight' but doc is only hair/khalitya
    if "weight" in q_tokens or "obesity" in q_tokens or "sthoulya" in q_tokens:
        if not any(w in blob for w in ("weight", "obesity", "sthoulya", "medha", "fat", "overweight")):
            return False
        if any(w in blob for w in ("hair", "khalitya", "dandruff", "darunaka", "bhringraj")):
            if not any(w in q_tokens for w in ("hair", "khalitya", "dandruff")):
                return False

    if "hair" in q_tokens or "khalitya" in q_tokens:
        if not any(w in blob for w in ("hair", "khalitya", "bhringraj", "darunaka")):
            return False

    if "acidity" in q_tokens or "amlapitta" in q_tokens:
        if not any(w in blob for w in ("acidity", "amlapitta", "hyperacidity", "heartburn")):
            return False

    return True


def filter_verified_hits(
    query: str,
    intent: QueryIntent,
    hits: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    verified = []
    for h in hits:
        score = float(h.get("match_score", 0) or 0)
        if score < MIN_MATCH_SCORE:
            continue
        if not document_matches_query(query, intent, h):
            continue
        verified.append(h)
    return verified
