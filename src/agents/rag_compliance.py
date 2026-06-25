from __future__ import annotations

import re

SAFE_FALLBACK = "No information found in our knowledge base"


def _tokenize(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z\u0900-\u097F]+", text) if len(t) > 2}


def claim_supported(claim: str, context_chunks: list[str], threshold: float = 0.35) -> bool:
    """Heuristic grounding: key claim tokens must appear in retrieved context."""
    claim_tokens = _tokenize(claim)
    if not claim_tokens:
        return False
    context_tokens: set[str] = set()
    for chunk in context_chunks:
        context_tokens |= _tokenize(chunk)
    overlap = claim_tokens & context_tokens
    return len(overlap) / len(claim_tokens) >= threshold


def run_rag_compliance_agent(completion: str, context_chunks: list[str]) -> str:
    """Strip ungrounded assertions; return safe fallback when hallucination detected."""
    sentences = re.split(r"(?<=[.!?।])\s+", completion.strip())
    grounded_parts = [s for s in sentences if claim_supported(s, context_chunks)]
    if not grounded_parts:
        return SAFE_FALLBACK
    return " ".join(grounded_parts).strip()
