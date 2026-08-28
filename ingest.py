"""
src/ingestion/ingest.py
--------------------------
Ingestion pipeline entrypoint (AC-01):
  load corpus -> chunk -> embed -> persist to Chroma (vector) + BM25 (lexical).

Idempotent: chunk_id is a deterministic hash of (doc_id, clause_id, part
index), so re-running ingestion with `upsert` never creates duplicate
vectors. The BM25 index is rebuilt from the same deterministic chunk list on
every run, so both indexes always stay in sync.

Usage:
    python -m src.ingestion.ingest
"""

from __future__ import annotations

import pickle
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

from src.config import CONFIG
from src.ingestion.chunker import Chunk, chunk_clauses
from src.ingestion.loader import load_corpus


def _tokenize(text: str) -> list[str]:
    return text.lower().split()


def build_chunks() -> list[Chunk]:
    clauses = load_corpus(CONFIG.corpus_dir, CONFIG.get("corpus.doc_glob", "*.md"))
    chunks = chunk_clauses(
        clauses,
        max_chars=CONFIG.get("chunking.max_chars", 900),
        overlap_chars=CONFIG.get("chunking.overlap_chars", 150),
        min_chars=CONFIG.get("chunking.min_chars", 120),
    )
    return chunks


def ingest() -> dict:
    chunks = build_chunks()
    if not chunks:
        raise RuntimeError("No chunks produced; check the corpus directory and chunker configuration.")

    model_name = CONFIG.get("embedding.model_name", "BAAI/bge-small-en-v1.5")
    embedder = SentenceTransformer(model_name)
    texts = [c.text for c in chunks]
    embeddings = embedder.encode(
        texts,
        normalize_embeddings=CONFIG.get("embedding.normalize", True),
        show_progress_bar=False,
    ).tolist()

    persist_dir = CONFIG.vector_store_dir
    persist_dir.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(persist_dir))
    collection_name = CONFIG.get("vector_store.collection_name", "hospital_policy_sop")
    collection = client.get_or_create_collection(collection_name)

    ids = [c.chunk_id for c in chunks]
    metadatas = [
        {
            "doc_id": c.doc_id,
            "doc_type": c.doc_type,
            "title": c.title,
            "owner_role": c.owner_role,
            "effective_date": c.effective_date,
            "clause_id": c.clause_id,
            "heading": c.heading,
            "source_path": c.source_path,
        }
        for c in chunks
    ]

    # Upsert => idempotent re-runs (AC-01: "re-runnable and idempotent")
    collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)

    # Lexical index (BM25), rebuilt fresh every run from the same chunk list
    tokenized_corpus = [_tokenize(t) for t in texts]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_path = persist_dir.parent / "bm25_index.pkl"
    with open(bm25_path, "wb") as f:
        pickle.dump({"bm25": bm25, "ids": ids, "texts": texts, "metadatas": metadatas}, f)

    return {
        "num_chunks": len(chunks),
        "num_documents": len(set(c.doc_id for c in chunks)),
        "vector_store_path": str(persist_dir),
        "bm25_index_path": str(bm25_path),
        "embedding_model": model_name,
    }


if __name__ == "__main__":
    stats = ingest()
    print("Ingestion complete:")
    for k, v in stats.items():
        print(f"  {k}: {v}")
