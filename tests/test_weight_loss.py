import asyncio

from src.config import get_settings
from src.database.lite_backend import LiteBackend, LiteEmbedder, LiteQdrantAdapter
from src.retrieval.hybrid_retriever import HybridRetriever
from src.agents.pipeline import AgentPipeline
from src.llm.vllm_client import VLLMClient


async def _run(q: str):
    s = get_settings()
    lite = LiteBackend()
    r = HybridRetriever(s, lite, LiteQdrantAdapter(lite), lite, LiteEmbedder())
    await r.load_corpus_index()
    p = AgentPipeline(r, VLLMClient(s), lite, lite)
    return await p.run_query(q)


def test_weight_loss_not_hair_remedies():
    res = asyncio.run(_run("weight loss"))
    assert res.grounded
    assert "Sthoulya" in res.conditions_detected
    names = [x.formulation_name.lower() for x in res.remedies]
    assert not any("bhringraj" in n for n in names)
    assert any("yava" in n or "guggulu" in n or "triphala" in n for n in names)


def test_weight_loss_answer_mentions_weight():
    res = asyncio.run(_run("weight loss"))
    assert "weight" in res.answer.lower() or "sthoulya" in res.answer.lower() or "obesity" in res.answer.lower()
