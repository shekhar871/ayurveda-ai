from __future__ import annotations

from typing import Any

from src.agents.answer_builder import build_grounded_answer
from src.agents.citation_verifier import format_citation, validate_remedy_citations
from src.agents.rag_compliance import SAFE_FALLBACK, run_rag_compliance_agent
from src.agents.schema_guard import QueryResponseSchema, RemedyOutputSchema
from src.llm.vllm_client import VLLMClient
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.match_validator import filter_verified_hits
from src.retrieval.query_analyzer import analyze_query


class AgentPipeline:
    def __init__(
        self,
        retriever: HybridRetriever,
        llm: VLLMClient,
        postgres: Any,
        neo4j: Any,
    ) -> None:
        self._retriever = retriever
        self._llm = llm
        self._pg = postgres
        self._neo4j = neo4j

    async def _graph_contraindication_notes(
        self, conditions: list[str], formulations: list[str]
    ) -> list[str]:
        notes = []
        if not conditions or not formulations:
            return notes
        blocked = await self._neo4j.check_contraindications(formulations, conditions)
        for b in blocked:
            notes.append(f"Avoid {b}: contraindicated for {', '.join(conditions)} per knowledge graph.")
        return notes

    async def run_query(
        self,
        query: str,
        user_id: str | None = None,
        season: str | None = None,
    ) -> QueryResponseSchema:
        query = query.strip()
        intent = analyze_query(query)
        profile = await self._pg.get_user_profile(user_id) if user_id else None

        raw_hits = await self._retriever.retrieve(
            query, user_profile=profile, top_k=8, query_intent=intent
        )

        if season:
            from src.agents.router import apply_ritucharya_boost

            raw_hits = apply_ritucharya_boost(raw_hits, season)

        context_hits = filter_verified_hits(query, intent, raw_hits)

        if not context_hits:
            return QueryResponseSchema(
                answer=(
                    f"No verified classical references for \"{query}\" are indexed in this system yet. "
                    "Try rephrasing with Ayurvedic terms (e.g. Sthoulya for weight, Khalitya for hair loss, "
                    "Amlapitta for acidity) or use System → Re-index after adding texts."
                ),
                remedies=[],
                citations=[],
                grounded=False,
                safety_notes=["Retrieval gate: zero passages passed condition and keyword validation."],
                query_intent=intent.intent,
                conditions_detected=intent.conditions,
                query=query,
                sources_used=0,
            )

        context_texts = [h.get("text", "") for h in context_hits]
        formulations = [
            (h.get("metadata") or {}).get("formulation")
            for h in context_hits
            if (h.get("metadata") or {}).get("formulation")
        ]

        profile_conditions = []
        if profile:
            vikriti = profile.get("vikriti") or {}
            if isinstance(vikriti, dict):
                profile_conditions = vikriti.get("aggravated", [])

        safety_notes = await self._graph_contraindication_notes(
            intent.conditions or profile_conditions, formulations
        )

        grounded_answer = build_grounded_answer(intent, context_hits)

        ayur_condition = intent.conditions[0] if intent.conditions else query

        remedies: list[RemedyOutputSchema] = []
        citations: list[str] = []
        seen_formulations: set[str] = set()

        for hit in context_hits[:8]:
            if not hit.get("grantha"):
                continue
            meta = hit.get("metadata") or {}
            content_type = meta.get("content_type", "")

            if intent.wants_remedy and content_type == "contraindication":
                continue
            if intent.is_contraindication and content_type == "indication":
                continue

            cite = format_citation(
                hit["grantha"], hit["sthana"], int(hit["adhyaya"]), int(hit["shloka"])
            )
            fname = meta.get("formulation") or "See classical text"
            if intent.is_contraindication and meta.get("formulation"):
                fname = f"Avoid: {fname}"

            dedupe_key = fname.lower().strip()
            if dedupe_key in seen_formulations:
                continue
            seen_formulations.add(dedupe_key)

            citations.append(cite)
            remedies.append(
                RemedyOutputSchema(
                    condition_confirmed=ayur_condition,
                    formulation_name=fname,
                    source_citation=cite,
                    modern_evidence_summary=hit.get("text", "")[:280],
                    duration_days=1 if intent.is_contraindication else 28,
                )
            )

        valid_cites, invalid_cites = await validate_remedy_citations(self._pg, citations)
        grounded = bool(valid_cites and remedies and grounded_answer != SAFE_FALLBACK)

        if invalid_cites:
            safety_notes.append(f"Invalid citations removed: {invalid_cites}")

        return QueryResponseSchema(
            answer=grounded_answer,
            remedies=remedies,
            citations=valid_cites,
            grounded=grounded,
            safety_notes=safety_notes,
            query_intent=intent.intent,
            conditions_detected=intent.conditions,
            query=query,
            sources_used=len(context_hits),
        )
