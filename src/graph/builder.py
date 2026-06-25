from __future__ import annotations

from src.database.neo4j_client import Neo4jClient


class GraphBuilder:
    def __init__(self, neo4j: Neo4jClient) -> None:
        self._neo4j = neo4j

    async def link_trial_to_herb(
        self,
        trial_id: str,
        formulation_name: str,
        p_value: float,
        efficacy_flag: bool,
    ) -> None:
        query = """
        MATCH (f:Formulation {name: $formulation_name})
        MERGE (t:ClinicalTrial {id: $trial_id})
        SET t.p_value = $p_value, t.efficacious = $efficacy_flag
        MERGE (t)-[:EVALUATES]->(f)
        MERGE (t)-[:VALIDATED_BY]-(f)
        """
        await self._neo4j.run_query(
            query,
            trial_id=trial_id,
            formulation_name=formulation_name,
            p_value=p_value,
            efficacy_flag=efficacy_flag,
        )

    async def seed_sample_graph(self) -> None:
        queries = [
            """
            MERGE (r:Roga {name: 'Khalitya'})
            MERGE (d:Dravya {name: 'Bhringraj'})
            SET d.rasa = 'Katu', d.virya = 'Ushna', d.vipaka = 'Katu'
            MERGE (f:Formulation {name: 'Bhringraj Taila'})
            MERGE (f)-[:INDICATED_IN]->(r)
            MERGE (f)-[:CONTAINS]->(d)
            MERGE (f)-[:CITED_IN]->(:Citation {grantha: 'AshtangaHridayam', adhyaya: 15, shloka: 42})
            """,
            """
            MERGE (c:ClinicalStudy {name: 'HairGrowthTrial2023'})
            MERGE (f:Formulation {name: 'Bhringraj Taila'})
            MERGE (t:ClinicalTrial {id: 'CT-HG-2023'})
            SET t.p_value = 0.02, t.efficacious = true
            MERGE (t)-[:EVALUATES]->(f)
            MERGE (f)-[:VALIDATED_BY]->(t)
            """,
            """
            MERGE (cond:Lakshana {name: 'Pitta aggravation'})
            MERGE (f:Formulation {name: 'Bhringraj Taila'})
            MERGE (f)-[:CONTRAINDICATED_FOR]->(cond)
            """,
        ]
        for q in queries:
            await self._neo4j.run_query(q)

    async def seed_full_graph(self) -> None:
        await self.seed_sample_graph()
        extra = [
            """
            MERGE (p:Lakshana {name: 'Pitta aggravation'})
            MERGE (f:Formulation {name: 'Trikatu Churna'})
            MERGE (f)-[:CONTRAINDICATED_FOR]->(p)
            """,
            """
            MERGE (r:Roga {name: 'Darunaka'})
            MERGE (f:Formulation {name: 'Malayaja Taila'})
            MERGE (f)-[:INDICATED_IN]->(r)
            """,
            """
            MERGE (d:Dravya {name: 'Trikatu'})
            MERGE (f:Formulation {name: 'Trikatu Churna'})
            MERGE (f)-[:CONTAINS]->(d)
            """,
        ]
        for q in extra:
            await self._neo4j.run_query(q)
