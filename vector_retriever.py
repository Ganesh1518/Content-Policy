"""
src/retrieval/vector_retriever.py
------------------------------------
Semantic (dense) retriever over the persisted Chroma vector store.
"""

from __future__ import annotations

import chromadb
from sentence_transformers import SentenceTransformer

from src.config import CONFIG
from src.retrieval.types import RetrievedChunk


class VectorRetriever:
    def __init__(self):
        persist_dir = CONFIG.vector_store_dir
        self._client = chromadb.PersistentClient(path=str(persist_dir))
        self._collection = self._client.get_or_create_collection(
            CONFIG.get("vector_store.collection_name", "hospital_policy_sop")
        )
        self._embedder = SentenceTransformer(CONFIG.get("embedding.model_name", "BAAI/bge-small-en-v1.5"))

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        query_emb = self._embedder.encode(
            [query], normalize_embeddings=CONFIG.get("embedding.normalize", True)
        ).tolist()
        result = self._collection.query(query_embeddings=query_emb, n_results=top_k)

        out: list[RetrievedChunk] = []
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        dists = result.get("distances", [[]])[0]
        for cid, doc, meta, dist in zip(ids, docs, metas, dists):
            # Chroma returns a distance (lower = closer); convert to a
            # similarity-style score in [0, 1] for fusion/threshold logic.
            score = max(0.0, 1.0 - dist)
            out.append(RetrievedChunk(chunk_id=cid, text=doc, metadata=meta, score=score, source="vector"))
        return out
