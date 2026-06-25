from __future__ import annotations

import re
from dataclasses import dataclass, field

NEGATION_NEARBY = (
    "worsen", "worsens", "avoid", "contraindicated", "not recommended", "must be avoided",
    "increase", "aggravates", "varjya", "न योज्य", "वर्जयेत", "वर्धन",
)

SYMPTOM_TREATMENT_DEFAULTS = (
    "acidity", "heartburn", "hyperacidity", "reflux", "indigestion", "bloating",
    "constipation", "headache", "insomnia", "anxiety", "amlapitta", "weight", "obesity",
    "diabetes", "arthritis", "cough", "fever", "skin", "hair", "dandruff",
)


@dataclass
class QueryIntent:
    raw_query: str
    intent: str  # contraindication | treatment | general
    conditions: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    required_terms: list[str] = field(default_factory=list)

    @property
    def is_contraindication(self) -> bool:
        return self.intent == "contraindication"

    @property
    def wants_remedy(self) -> bool:
        return self.intent in ("treatment", "general")


CONDITION_ALIASES: dict[str, list[str]] = {
    "Amlapitta": ["acidity", "hyperacidity", "heartburn", "acid reflux", "amlapitta", "amla pitta", "अम्लपित्त", "gerd"],
    "Sthoulya": ["weight loss", "lose weight", "obesity", "overweight", "sthoulya", "medha", "fat reduction", "slimming"],
    "Khalitya": ["hair loss", "khalitya", "baldness", "खालित्य", "alopecia"],
    "Darunaka": ["darunaka", "dandruff", "दारुणक", "scalp flakes"],
    "Pitta aggravation": ["pitta aggravation", "pitta prakopa", "aggravated pitta"],
    "Vata aggravation": ["vata aggravation", "vata prakopa"],
    "Kapha aggravation": ["kapha aggravation", "kapha prakopa"],
    "Prameha": ["diabetes", "prameha", "blood sugar", "madhumeha"],
}

INTENT_KEYWORDS = {
    "contraindication": [
        "contraindication", "contraindicated", "what to avoid", "should not take",
        "should not use", "do not use", "not recommended", "varjya", "वर्ज्य",
    ],
    "treatment": [
        "treatment", "remedy", "remedies", "cure", "help", "used for", "indicated",
        "therapy", "medicine", "what to take", "recommend", "for",
    ],
}


def is_negation_only_match(query: str, text: str) -> bool:
    lower = text.lower()
    q = query.lower().strip()
    for term in _tokens(q):
        if len(term) < 4:
            continue
        if term not in lower:
            continue
        idx = lower.find(term)
        window = lower[max(0, idx - 55) : idx + len(term) + 55]
        if any(n in window for n in NEGATION_NEARBY):
            return True
    return False


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z\u0900-\u097F]{2,}", text.lower())]


def analyze_query(query: str) -> QueryIntent:
    lower = query.lower().strip()
    intent = "treatment"  # default: user wants actionable guidance

    if any(k in lower for k in INTENT_KEYWORDS["contraindication"]):
        intent = "contraindication"
    elif any(k in lower for k in INTENT_KEYWORDS["treatment"]):
        intent = "treatment"

    conditions: list[str] = []
    topics: list[str] = []
    for canonical, aliases in CONDITION_ALIASES.items():
        if any(a in lower for a in aliases):
            conditions.append(canonical)
            topics.append(canonical.lower().replace(" ", "_"))

    required = list(dict.fromkeys(_tokens(lower)))[:14]

    return QueryIntent(
        raw_query=query,
        intent=intent,
        conditions=conditions,
        topics=list(dict.fromkeys(topics)),
        required_terms=required,
    )


def relevance_score(query_intent: QueryIntent, hit: dict) -> float:
    text = (hit.get("text") or "").lower()
    meta = hit.get("metadata") or {}
    if not isinstance(meta, dict):
        meta = {}
    meta_topics = [str(t).lower() for t in meta.get("topics", [])]
    meta_conditions = [str(c).lower() for c in meta.get("conditions", [])]
    content_type = str(meta.get("content_type", "")).lower()
    blob = " ".join([text] + meta_topics + meta_conditions)

    q_terms = set(query_intent.required_terms)
    blob_tokens = set(_tokens(blob))
    overlap = len(q_terms & blob_tokens) / max(len(q_terms), 1)
    score = overlap * 0.5

    for cond in query_intent.conditions:
        if cond.lower() in blob or cond.lower() in " ".join(meta_conditions):
            score += 0.3

    if query_intent.wants_remedy and content_type == "indication":
        score += 0.25
    if query_intent.is_contraindication and content_type == "contraindication":
        score += 0.3

    return min(max(score, 0), 1.0)
