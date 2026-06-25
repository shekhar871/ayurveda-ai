from __future__ import annotations

import json
import logging

import httpx
from openai import AsyncOpenAI

from src.config import Settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an Ayurvedic clinical assistant. Answer ONLY from the provided context.
Map colloquial symptoms to classical terms (Khalitya, Darunaka). Every claim must be supportable by context.
Include citation coordinates when possible: Grantha | Sthana | Adhyaya N | Shloka N.
Do not invent formulations, dosages, or instant cures."""


class VLLMClient:
    """OpenAI-compatible client for local vLLM; rule-based fallback without GPU."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = AsyncOpenAI(
            base_url=settings.vllm_url,
            api_key="not-needed",
        )

    async def generate_remedy(
        self,
        query: str,
        condition: str,
        context_chunks: list[str],
    ) -> str:
        context_block = "\n---\n".join(context_chunks[:6])
        user_msg = (
            f"User query: {query}\n"
            f"Mapped condition: {condition}\n\n"
            f"Retrieved context:\n{context_block}\n\n"
            "Provide a concise, grounded recommendation."
        )
        try:
            resp = await self._client.chat.completions.create(
                model=self._settings.vllm_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.2,
                max_tokens=512,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            logger.warning("vLLM unavailable (%s), using template fallback", exc)
            return self._fallback_response(condition, context_chunks)

    def _fallback_response(self, condition: str, context_chunks: list[str]) -> str:
        if not context_chunks:
            return "No information found in our knowledge base."
        excerpt = context_chunks[0][:400]
        return (
            f"Based on classical references for {condition}: {excerpt} "
            "Consult a qualified Vaidya before starting any protocol."
        )
