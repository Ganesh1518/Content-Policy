"""
src/retrieval/bm25_retriever.py
----------------------------------
Lexical (BM25) retriever. Loads the index persisted by src/ingestion/ingest.py.
"""

from __future__ import annotations

import pickle

from src.config import CONFIG
from src.retrieval.types import RetrievedChunk


class BM25Retriever:
    def __init__(self):
        bm25_path = CONFIG.vector_store_dir.parent / "bm25_index.pkl"
        if not bm25_path.exists():
            raise FileNotFoundError(
                f"BM25 index not found at {bm25_path}. Run `python -m src.ingestion.ingest` first."
            )
        with open(bm25_path, "rb") as f:
            payload = pickle.load(f)
        self._bm25 = payload["bm25"]
        self._ids = payload["ids"]
        self._texts = payload["texts"]
        self._metadatas = payload["metadatas"]

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        tokens = query.lower().split()
        scores = self._bm25.get_scores(tokens)
        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        max_score = max(scores) if len(scores) and max(scores) > 0 else 1.0
        out = []
        for i in ranked:
            norm_score = float(scores[i]) / max_score if max_score else 0.0
            out.append(
                RetrievedChunk(
                    chunk_id=self._ids[i],
                    text=self._texts[i],
                    metadata=self._metadatas[i],
                    score=norm_score,
                    source="bm25",
                )
            )
        return out
