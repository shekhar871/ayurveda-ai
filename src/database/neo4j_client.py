from __future__ import annotations

from typing import Any

from neo4j import AsyncGraphDatabase

from src.config import Settings


class Neo4jClient:
    def __init__(self, settings: Settings) -> None:
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    async def connect(self) -> None:
        async with self._driver.session() as session:
            await session.run("RETURN 1")

    async def close(self) -> None:
        await self._driver.close()

    async def run_query(self, query: str, **params: Any) -> list[dict[str, Any]]:
        async with self._driver.session() as session:
            result = await session.run(query, **params)
            records = await result.data()
            return records

    async def check_contraindications(
        self, formulation_names: list[str], user_conditions: list[str]
    ) -> list[str]:
        if not formulation_names or not user_conditions:
            return []
        query = """
        UNWIND $formulations AS fname
        MATCH (f:Formulation {name: fname})-[:CONTRAINDICATED_FOR]->(c)
        WHERE c.name IN $conditions
        RETURN DISTINCT fname AS blocked_formulation, c.name AS condition
        """
        rows = await self.run_query(
            query, formulations=formulation_names, conditions=user_conditions
        )
        return [r["blocked_formulation"] for r in rows]

    async def get_formulation_attributes(self, name: str) -> dict[str, Any]:
        query = """
        MATCH (d:Dravya {name: $name})
        OPTIONAL MATCH (d)-[:HAS_RASA]->(r:Rasa)
        OPTIONAL MATCH (d)-[:HAS_GUNA]->(g:Guna)
        RETURN d.name AS name, collect(DISTINCT r.name) AS rasa,
               collect(DISTINCT g.name) AS guna
        """
        rows = await self.run_query(query, name=name)
        return rows[0] if rows else {}

    async def find_alternative_formulations(
        self,
        roga: str,
        blocked: list[str],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        query = """
        MATCH (r:Roga {name: $roga})<-[:INDICATED_IN]-(f:Formulation)
        WHERE NOT f.name IN $blocked
        OPTIONAL MATCH (f)-[:VALIDATED_BY]->(t:ClinicalTrial)
        WITH f, count(t) AS trial_count
        OPTIONAL MATCH (f)-[:CITED_IN]->(c)
        WITH f, trial_count, count(c) AS citation_depth
        RETURN f.name AS formulation, trial_count, citation_depth
        ORDER BY trial_count DESC, citation_depth DESC
        LIMIT $limit
        """
        return await self.run_query(query, roga=roga, blocked=blocked, limit=limit)
