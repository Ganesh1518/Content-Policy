"""
src/retrieval/fusion.py
--------------------------
Reciprocal Rank Fusion (RRF) of the lexical (BM25) and semantic (vector)
candidate lists, per AC-03.

RRF score for a document d across result lists R = { r_1, r_2, ... }:
    RRF(d) = sum_over_lists( 1 / (k + rank_of_d_in_list) )

k (rrf_k) dampens the influence of very high ranks in a single list, which
is the standard, parameter-light way to fuse heterogeneous scoring scales
(BM25 scores and cosine-similarity scores are not directly comparable, so
fusing on RANK rather than raw score avoids that scale mismatch).
"""

from __future__ import annotations

from src.retrieval.types import RetrievedChunk


def reciprocal_rank_fusion(
    result_lists: list[list[RetrievedChunk]],
    k: int = 60,
) -> list[RetrievedChunk]:
    scores: dict[str, float] = {}
    best_chunk: dict[str, RetrievedChunk] = {}

    for result_list in result_lists:
        for rank, chunk in enumerate(result_list, start=1):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1.0 / (k + rank)
            # keep whichever record we saw first for text/metadata purposes
            best_chunk.setdefault(chunk.chunk_id, chunk)

    fused: list[RetrievedChunk] = []
    for chunk_id, rrf_score in scores.items():
        base = best_chunk[chunk_id]
        fused.append(
            RetrievedChunk(
                chunk_id=base.chunk_id,
                text=base.text,
                metadata=base.metadata,
                score=rrf_score,
                source="fused",
            )
        )

    fused.sort(key=lambda c: c.score, reverse=True)
    return fused
