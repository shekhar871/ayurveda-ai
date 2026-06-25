from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any

from src.embeddings.hash_embedder import hash_embed, hash_embed_batch
from src.ingestion.text_splitter import VerseEnvelope

STORE_PATH = Path(__file__).resolve().parents[2] / "data" / "lite_store.json"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class LiteBackend:
    """File-backed store — runs with zero Docker services."""

    def __init__(self, store_path: Path | None = None) -> None:
        self._path = store_path or STORE_PATH
        self._data: dict[str, Any] = {
            "verses": [],
            "citations": [],
            "profiles": {},
            "feedback": [],
            "graph": {
                "formulations": {
                    "Bhringraj Taila": {
                        "indicated_in": ["Khalitya"],
                        "contraindicated_for": ["Pitta aggravation"],
                        "trials": 1,
                        "citations": 1,
                    }
                },
            },
        }
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            self._data = json.loads(self._path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _verse_key(self, v: dict) -> str:
        return f"{v['grantha']}:{v['sthana']}:{v['adhyaya']}:{v['shloka']}:{v['language']}"

    def _write_verse(self, envelope: VerseEnvelope, embedding: list[float]) -> int:
        key = f"{envelope.grantha}:{envelope.sthana}:{envelope.adhyaya}:{envelope.shloka}:{envelope.language}"
        self._data["verses"] = [v for v in self._data["verses"] if self._verse_key(v) != key]
        vid = len(self._data["verses"]) + 1
        self._data["verses"].append(
            {
                "id": vid,
                "text": envelope.text,
                "grantha": envelope.grantha,
                "sthana": envelope.sthana,
                "adhyaya": envelope.adhyaya,
                "shloka": envelope.shloka,
                "language": envelope.language,
                "metadata": envelope.metadata,
                "embedding": embedding,
            }
        )
        self._save()
        return vid

    async def connect(self) -> None:
        pass

    async def close(self) -> None:
        self._save()

    async def upsert_verse(self, envelope: VerseEnvelope, embedding: list[float]) -> int:
        return self._write_verse(envelope, embedding)

    def upsert_verse_sync(self, envelope: VerseEnvelope, embedding: list[float]) -> None:
        self._write_verse(envelope, embedding)

    async def fts_search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        import re

        q_tokens = [t for t in re.findall(r"[a-zA-Z\u0900-\u097F]{2,}", query.lower())]
        hits = []
        for v in self._data["verses"]:
            meta = v.get("metadata") or {}
            blob = " ".join(
                [
                    v["text"].lower(),
                    " ".join(str(t) for t in meta.get("topics", [])),
                    " ".join(str(c) for c in meta.get("conditions", [])),
                    str(meta.get("content_type", "")),
                    str(meta.get("formulation", "")),
                ]
            ).lower()
            score = sum(1 for t in q_tokens if t in blob)
            if score > 0:
                hits.append({**v, "rank": score / max(len(q_tokens), 1)})
        hits.sort(key=lambda x: x["rank"], reverse=True)
        return hits[:limit]

    async def register_citation(self, grantha: str, sthana: str, adhyaya: int, shloka: int) -> None:
        for c in self._data["citations"]:
            if c["grantha"] == grantha and c["sthana"] == sthana and c["adhyaya"] == adhyaya:
                c["max_shloka"] = max(c["max_shloka"], shloka)
                self._save()
                return
        self._data["citations"].append(
            {"grantha": grantha, "sthana": sthana, "adhyaya": adhyaya, "max_shloka": shloka}
        )
        self._save()

    async def validate_citation(self, grantha: str, sthana: str, adhyaya: int, shloka: int) -> bool:
        for c in self._data["citations"]:
            if (
                c["grantha"].lower() == grantha.lower()
                and c["sthana"].lower() == sthana.lower()
                and c["adhyaya"] == adhyaya
                and shloka <= c["max_shloka"]
            ):
                return True
        return False

    async def get_user_profile(self, user_id: str) -> dict[str, Any] | None:
        return self._data["profiles"].get(user_id)

    async def upsert_user_profile(self, user_id: str | None, data: dict[str, Any]) -> str:
        uid = user_id or str(uuid.uuid4())
        existing = self._data["profiles"].get(uid, {})
        self._data["profiles"][uid] = {
            "user_id": uid,
            "prakriti": data.get("prakriti", {}),
            "vikriti": data.get("vikriti", {}),
            "allergies": data.get("allergies", []),
            "contraindications": data.get("contraindications", []),
            "active_protocol": data.get("active_protocol", {}),
            "timeline": existing.get("timeline", []),
            "efficacy_scores": existing.get("efficacy_scores", {}),
        }
        self._save()
        return uid

    async def record_feedback(
        self, user_id: str, formulation_name: str, outcome: str, checkpoint_day: int, notes: str = ""
    ) -> None:
        self._data["feedback"].append(
            {
                "user_id": user_id,
                "formulation_name": formulation_name,
                "outcome": outcome,
                "checkpoint_day": checkpoint_day,
                "notes": notes,
            }
        )
        self._save()

    async def boost_efficacy(self, user_id: str, formulation_name: str, delta: float) -> None:
        profile = self._data["profiles"].setdefault(user_id, {"efficacy_scores": {}})
        scores = profile.setdefault("efficacy_scores", {})
        scores[formulation_name] = scores.get(formulation_name, 0) + delta
        self._save()

    async def update_timeline(self, user_id: str, timeline: list[dict]) -> None:
        profile = self._data["profiles"].setdefault(user_id, {})
        profile["timeline"] = timeline
        profile["active_protocol"] = timeline[-1] if timeline else {}
        self._save()

    async def ensure_collection(self) -> None:
        pass

    def dense_search(self, query_vector: list[float], limit: int = 10) -> list[dict[str, Any]]:
        scored = []
        for v in self._data["verses"]:
            emb = v.get("embedding") or hash_embed(v["text"])
            scored.append(
                {
                    "score": _cosine(query_vector, emb),
                    "text": v["text"],
                    "grantha": v["grantha"],
                    "sthana": v["sthana"],
                    "adhyaya": v["adhyaya"],
                    "shloka": v["shloka"],
                    "language": v["language"],
                    "metadata": v.get("metadata", {}),
                }
            )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]

    async def check_contraindications(
        self, formulation_names: list[str], user_conditions: list[str]
    ) -> list[str]:
        blocked = []
        graph = self._data["graph"]["formulations"]
        for name in formulation_names:
            info = graph.get(name, {})
            if set(info.get("contraindicated_for", [])) & set(user_conditions):
                blocked.append(name)
        return blocked

    async def get_formulation_attributes(self, name: str) -> dict[str, Any]:
        return {"name": name, "rasa": ["Katu"], "guna": ["Laghu"]}

    async def find_alternative_formulations(
        self, roga: str, blocked: list[str], limit: int = 5
    ) -> list[dict[str, Any]]:
        alts = []
        for fname, info in self._data["graph"]["formulations"].items():
            if roga in info.get("indicated_in", []) and fname not in blocked:
                alts.append(
                    {
                        "formulation": fname,
                        "trial_count": info.get("trials", 0),
                        "citation_depth": info.get("citations", 0),
                    }
                )
        alts.sort(key=lambda x: (x["trial_count"], x["citation_depth"]), reverse=True)
        return alts[:limit]


class LiteEmbedder:
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return hash_embed_batch(texts)

    async def embed_query(self, text: str) -> list[float]:
        return hash_embed(text)


class LiteQdrantAdapter:
    """Wraps LiteBackend for QdrantStore.sync API."""

    def __init__(self, backend: LiteBackend) -> None:
        self._backend = backend

    async def ensure_collection(self) -> None:
        pass

    def upsert_verse(self, envelope: VerseEnvelope, embedding: list[float]) -> None:
        self._backend.upsert_verse_sync(envelope, embedding)

    def dense_search(self, query_vector: list[float], limit: int = 10) -> list[dict[str, Any]]:
        return self._backend.dense_search(query_vector, limit)
