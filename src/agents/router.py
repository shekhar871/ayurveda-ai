from __future__ import annotations

from typing import Any


async def resolve_alternative_pathway(
    neo4j: Any,
    postgres: Any,
    user_id: str,
    current_protocol_id: str,
    observed_imbalance: str,
    user_conditions: list[str] | None = None,
) -> dict[str, Any]:
    """
    Alternative treatment selector on progress failure.
    1. Query Neo4j for alternatives
    2. Strip counter-indicated formulations
    3. Sort by citation depth + trial scores
    4. Update user timeline
    """
    roga = observed_imbalance or "Khalitya"
    profile = await postgres.get_user_profile(user_id)
    conditions = list(user_conditions or [])
    if profile:
        vikriti = profile.get("vikriti") or {}
        if isinstance(vikriti, dict):
            conditions.extend(vikriti.get("aggravated", []))

    candidates = await neo4j.find_alternative_formulations(roga=roga, blocked=[current_protocol_id])
    names = [c["formulation"] for c in candidates]
    blocked = await neo4j.check_contraindications(names, conditions)
    safe = [c for c in candidates if c["formulation"] not in blocked]

    if not safe:
        return {"status": "no_safe_alternative", "timeline": profile.get("timeline", []) if profile else []}

    chosen = safe[0]
    timeline = list((profile or {}).get("timeline") or [])
    entry = {
        "protocol_id": chosen["formulation"],
        "replaced": current_protocol_id,
        "reason": observed_imbalance,
        "citation_depth": chosen.get("citation_depth", 0),
        "trial_count": chosen.get("trial_count", 0),
    }
    timeline.append(entry)
    await postgres.update_timeline(user_id, timeline)

    return {
        "status": "alternative_activated",
        "new_protocol": chosen["formulation"],
        "timeline": timeline,
        "blocked": blocked,
    }


def apply_ritucharya_boost(
    recommendations: list[dict[str, Any]],
    season: str,
) -> list[dict[str, Any]]:
    """Rank boost for seasonal (*Ritucharya*) alignment."""
    season_prefs = {
        "varsha": ["warm", "light", "digestive"],
        "sharad": ["cooling", "pitta"],
        "hemanta": ["warming", "unctuous"],
        "shishira": ["warming", "unctuous"],
        "vasanta": ["detox", "kapha"],
        "grishma": ["cooling", "hydrating"],
    }
    prefs = set(season_prefs.get(season.lower(), []))
    for rec in recommendations:
        tags = set((rec.get("metadata") or {}).get("season_tags", []))
        if tags & prefs:
            rec["fused_score"] = rec.get("fused_score", 0) + 0.15
    return sorted(recommendations, key=lambda x: x.get("fused_score", 0), reverse=True)
