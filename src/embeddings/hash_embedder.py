from __future__ import annotations

import hashlib
import math
import re


def hash_embed(text: str, dim: int = 384) -> list[float]:
    """Fast local embeddings — no model download required."""
    vec = [0.0] * dim
    tokens = re.findall(r"[a-zA-Z\u0900-\u097F]+", text.lower())
    for token in tokens:
        digest = hashlib.sha256(token.encode()).digest()
        for i in range(dim):
            byte = digest[i % len(digest)]
            vec[i] += (byte / 127.5) - 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def hash_embed_batch(texts: list[str], dim: int = 384) -> list[list[float]]:
    return [hash_embed(t, dim=dim) for t in texts]
