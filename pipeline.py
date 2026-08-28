"""
src/pipeline.py
------------------
End-to-end orchestrator wiring together every stage required by the
business case:
    query transformation -> hybrid retrieval (BM25 + vector) -> RRF fusion ->
    cross-encoder reranking -> grounded, structured generation with abstention.

Usage (CLI):
    python -m src.pipeline "What is the hand-hygiene protocol before a procedure?"
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass

from src.config import CONFIG
from src.generation.generator import generate_answer
from src.generation.schema import AnswerResponse
from src.retrieval.bm25_retriever import BM25Retriever
from src.retrieval.fusion import reciprocal_rank_fusion
from src.retrieval.query_transform import transform_query
from src.retrieval.reranker import rerank
from src.retrieval.types import RetrievedChunk
from src.retrieval.vector_retriever import VectorRetriever

logging.basicConfig(level=CONFIG.get("logging.level", "INFO"))
logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    question: str
    sub_queries: list[str]
    retrieved_chunks: list[RetrievedChunk]
    answer: AnswerResponse


class RAGPipeline:
    """Loads retrievers once; call `.ask()` per query."""

    def __init__(self):
        self._vector = VectorRetriever()
        self._bm25 = BM25Retriever()

    def _retrieve(self, sub_queries: list[str]) -> list[RetrievedChunk]:
        pool_size = CONFIG.get("fusion.candidate_pool_per_retriever", 20)
        rrf_k = CONFIG.get("fusion.rrf_k", 60)
        top_k_in = CONFIG.get("reranker.top_k_in", 20)
        top_k_out = CONFIG.get("reranker.top_k_out", 5)

        all_fused: list[RetrievedChunk] = []
        for q in sub_queries:
            vec_results = self._vector.retrieve(q, top_k=pool_size)
            bm25_results = self._bm25.retrieve(q, top_k=pool_size)
            fused = reciprocal_rank_fusion([vec_results, bm25_results], k=rrf_k)
            all_fused.extend(fused[:top_k_in])

        # de-duplicate by chunk_id, keeping the highest fused score
        best: dict[str, RetrievedChunk] = {}
        for c in all_fused:
            if c.chunk_id not in best or c.score > best[c.chunk_id].score:
                best[c.chunk_id] = c
        candidates = sorted(best.values(), key=lambda c: c.score, reverse=True)[:top_k_in]

        combined_query = " ".join(sub_queries)
        return rerank(combined_query, candidates, top_k_out=top_k_out)

    def ask(self, question: str, model_name: str | None = None) -> PipelineResult:
        sub_queries = transform_query(question)
        top_chunks = self._retrieve(sub_queries)
        answer = generate_answer(question, top_chunks, model_name=model_name)
        return PipelineResult(
            question=question,
            sub_queries=sub_queries,
            retrieved_chunks=top_chunks,
            answer=answer,
        )


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m src.pipeline "<question>"')
        sys.exit(1)
    question = " ".join(sys.argv[1:])
    pipeline = RAGPipeline()
    result = pipeline.ask(question)

    print(f"\nQuestion: {result.question}")
    print(f"Sub-queries used: {result.sub_queries}")
    print("\n--- Retrieved chunks ---")
    for c in result.retrieved_chunks:
        print(f"  [{c.score:.3f}] {c.metadata.get('doc_id')} §{c.metadata.get('clause_id')}")
    print("\n--- Answer ---")
    print(result.answer.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
