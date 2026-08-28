"""
src/retrieval/types.py
--------------------------
Shared, dependency-light data type used across retrieval and generation
modules. Kept separate from vector_retriever.py (which imports chromadb /
sentence-transformers) so downstream modules that only need the TYPE — not
a live vector store connection — don't have to pull in heavy ML libraries.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    metadata: dict
    score: float
    source: str  # "vector" | "bm25" | "fused" | "reranked"
