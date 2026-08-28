"""
src/retrieval/reranker.py
----------------------------
Cross-encoder reranking stage (AC-04). Takes the fused RRF candidate pool and
re-scores each (query, chunk) pair jointly, which is far more precise than
the bi-encoder / BM25 scores used for first-stage retrieval. The reranked
top-K is what actually reaches the generator.
"""

from __future__ import annotations

from sentence_transformers import CrossEncoder

from src.config import CONFIG
from src.retrieval.types import RetrievedChunk

_MODEL_CACHE: dict[str, CrossEncoder] = {}


def _get_model(model_name: str) -> CrossEncoder:
    if model_name not in _MODEL_CACHE:
        _MODEL_CACHE[model_name] = CrossEncoder(model_name)
    return _MODEL_CACHE[model_name]


def rerank(query: str, candidates: list[RetrievedChunk], top_k_out: int | None = None) -> list[RetrievedChunk]:
    if not candidates:
        return []

    model_name = CONFIG.get("reranker.model_name", "cross-encoder/ms-marco-MiniLM-L-6-v2")
    top_k_out = top_k_out or CONFIG.get("reranker.top_k_out", 5)
    model = _get_model(model_name)

    pairs = [[query, c.text] for c in candidates]
    raw_scores = model.predict(pairs)

    # Squash to [0, 1] via sigmoid so downstream abstention thresholds
    # (config: retrieval.score_threshold) are stable and interpretable.
    import math

    def sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    reranked = []
    for c, raw in zip(candidates, raw_scores):
        reranked.append(
            RetrievedChunk(
                chunk_id=c.chunk_id,
                text=c.text,
                metadata=c.metadata,
                score=sigmoid(float(raw)),
                source="reranked",
            )
        )
    reranked.sort(key=lambda c: c.score, reverse=True)
    return reranked[:top_k_out]
