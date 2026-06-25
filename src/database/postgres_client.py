from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import Settings
from src.ingestion.text_splitter import VerseEnvelope


class PostgresClient:
    def __init__(self, settings: Settings) -> None:
        self._engine = create_async_engine(settings.postgres_dsn, pool_size=10, max_overflow=20)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    async def connect(self) -> None:
        async with self._engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

    async def close(self) -> None:
        await self._engine.dispose()

    async def upsert_verse(self, envelope: VerseEnvelope, embedding: list[float]) -> int:
        vec_literal = "[" + ",".join(str(v) for v in embedding) + "]"
        q = text("""
            INSERT INTO verse_index (text, grantha, sthana, adhyaya, shloka, language, metadata, embedding)
            VALUES (:text, :grantha, :sthana, :adhyaya, :shloka, :language, CAST(:metadata AS jsonb), CAST(:embedding AS vector))
            ON CONFLICT (grantha, sthana, adhyaya, shloka, language)
            DO UPDATE SET text = EXCLUDED.text, metadata = EXCLUDED.metadata, embedding = EXCLUDED.embedding
            RETURNING id
        """)
        async with self._session_factory() as session:
            result = await session.execute(
                q,
                {
                    "text": envelope.text,
                    "grantha": envelope.grantha,
                    "sthana": envelope.sthana,
                    "adhyaya": envelope.adhyaya,
                    "shloka": envelope.shloka,
                    "language": envelope.language,
                    "metadata": json.dumps(envelope.metadata),
                    "embedding": vec_literal,
                },
            )
            await session.commit()
            row = result.fetchone()
            return int(row[0])

    async def fts_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        q = text("""
            SELECT id, text, grantha, sthana, adhyaya, shloka, language, metadata,
                   ts_rank(fts, plainto_tsquery('simple', :query)) AS rank
            FROM verse_index
            WHERE fts @@ plainto_tsquery('simple', :query)
            ORDER BY rank DESC
            LIMIT :limit
        """)
        async with self._session_factory() as session:
            result = await session.execute(q, {"query": query, "limit": limit})
            return [dict(r._mapping) for r in result.fetchall()]

    async def register_citation(self, grantha: str, sthana: str, adhyaya: int, shloka: int) -> None:
        q = text("""
            INSERT INTO citation_master (grantha, sthana, adhyaya, max_shloka)
            VALUES (:grantha, :sthana, :adhyaya, :shloka)
            ON CONFLICT (grantha, sthana, adhyaya)
            DO UPDATE SET max_shloka = GREATEST(citation_master.max_shloka, EXCLUDED.max_shloka)
        """)
        async with self._session_factory() as session:
            await session.execute(
                q,
                {"grantha": grantha, "sthana": sthana, "adhyaya": adhyaya, "shloka": shloka},
            )
            await session.commit()

    async def validate_citation(self, grantha: str, sthana: str, adhyaya: int, shloka: int) -> bool:
        q = text("""
            SELECT 1 FROM citation_master
            WHERE grantha = :grantha AND sthana = :sthana AND adhyaya = :adhyaya
              AND :shloka <= max_shloka
        """)
        async with self._session_factory() as session:
            result = await session.execute(
                q,
                {"grantha": grantha, "sthana": sthana, "adhyaya": adhyaya, "shloka": shloka},
            )
            return result.fetchone() is not None

    async def get_user_profile(self, user_id: str) -> dict[str, Any] | None:
        q = text("SELECT * FROM user_profiles WHERE user_id = CAST(:uid AS uuid)")
        async with self._session_factory() as session:
            result = await session.execute(q, {"uid": user_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None

    async def upsert_user_profile(self, user_id: str | None, data: dict[str, Any]) -> str:
        uid = user_id or str(uuid.uuid4())
        q = text("""
            INSERT INTO user_profiles (user_id, prakriti, vikriti, allergies, contraindications, active_protocol)
            VALUES (CAST(:uid AS uuid), CAST(:prakriti AS jsonb), CAST(:vikriti AS jsonb),
                    :allergies, :contraindications, CAST(:protocol AS jsonb))
            ON CONFLICT (user_id) DO UPDATE SET
                prakriti = EXCLUDED.prakriti,
                vikriti = EXCLUDED.vikriti,
                allergies = EXCLUDED.allergies,
                contraindications = EXCLUDED.contraindications,
                active_protocol = EXCLUDED.active_protocol
            RETURNING user_id::text
        """)
        async with self._session_factory() as session:
            result = await session.execute(
                q,
                {
                    "uid": uid,
                    "prakriti": json.dumps(data.get("prakriti", {})),
                    "vikriti": json.dumps(data.get("vikriti", {})),
                    "allergies": data.get("allergies", []),
                    "contraindications": data.get("contraindications", []),
                    "protocol": json.dumps(data.get("active_protocol", {})),
                },
            )
            await session.commit()
            return str(result.fetchone()[0])

    async def record_feedback(
        self, user_id: str, formulation_name: str, outcome: str, checkpoint_day: int, notes: str = ""
    ) -> None:
        q = text("""
            INSERT INTO interaction_feedback (user_id, formulation_name, outcome, checkpoint_day, notes)
            VALUES (CAST(:uid AS uuid), :formulation, :outcome, :day, :notes)
        """)
        async with self._session_factory() as session:
            await session.execute(
                q,
                {
                    "uid": user_id,
                    "formulation": formulation_name,
                    "outcome": outcome,
                    "day": checkpoint_day,
                    "notes": notes,
                },
            )
            await session.commit()

    async def boost_efficacy(self, user_id: str, formulation_name: str, delta: float) -> None:
        q = text("""
            UPDATE user_profiles
            SET efficacy_scores = efficacy_scores || CAST(:patch AS jsonb)
            WHERE user_id = CAST(:uid AS uuid)
        """)
        patch = json.dumps({formulation_name: delta})
        async with self._session_factory() as session:
            await session.execute(q, {"uid": user_id, "patch": patch})
            await session.commit()

    async def update_timeline(self, user_id: str, timeline: list[dict]) -> None:
        q = text("""
            UPDATE user_profiles SET timeline = CAST(:timeline AS jsonb), active_protocol = CAST(:protocol AS jsonb)
            WHERE user_id = CAST(:uid AS uuid)
        """)
        protocol = timeline[-1] if timeline else {}
        async with self._session_factory() as session:
            await session.execute(
                q,
                {
                    "uid": user_id,
                    "timeline": json.dumps(timeline),
                    "protocol": json.dumps(protocol),
                },
            )
            await session.commit()
