from __future__ import annotations

from src.agents.rag_compliance import SAFE_FALLBACK
from src.retrieval.query_analyzer import QueryIntent


def build_grounded_answer(query_intent: QueryIntent, context_hits: list[dict]) -> str:
    if not context_hits:
        return SAFE_FALLBACK

    hits = [h for h in context_hits if h.get("text")]
    if not hits:
        return SAFE_FALLBACK

    if query_intent.is_contraindication:
        lines = [
            f"Contraindications for {', '.join(query_intent.conditions) or query_intent.raw_query}:"
        ]
        for h in hits[:4]:
            t = h.get("text", "").strip()
            fname = (h.get("metadata") or {}).get("formulation")
            if fname:
                lines.append(f"• Avoid {fname}: {t[:200]}")
            else:
                lines.append(f"• {t[:200]}")
        lines.append("Consult a qualified Vaidya before changing any protocol.")
        return " ".join(lines)

    if query_intent.wants_remedy:
        label = query_intent.conditions[0] if query_intent.conditions else query_intent.raw_query
        lines = [f"Classical references for {label}:"]
        seen: set[str] = set()
        for h in hits:
            if len(lines) > 5:
                break
            t = h.get("text", "").strip()
            fname = (h.get("metadata") or {}).get("formulation")
            key = (fname or t[:40]).lower()
            if key in seen:
                continue
            seen.add(key)
            if fname:
                lines.append(f"• {fname}: {t[:220]}")
            else:
                lines.append(f"• {t[:220]}")
        lines.append("Consult a qualified Vaidya for personalized dosing.")
        return " ".join(lines)

    return SAFE_FALLBACK
