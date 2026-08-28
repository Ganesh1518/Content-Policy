"""
eval/ragas_metrics.py
------------------------
Wraps the RAGAS library to compute the four required metrics (AC-09):
  - context_precision
  - context_recall
  - faithfulness
  - answer_relevancy

The judge LLM is Gemini (config: evaluation.judge_model), consistent with
Section 9 of the business case ("Rubric parameters scored with Google
Gemini, not Claude" — the same discipline is applied to our own eval
judge so evaluation results are provider-consistent).
"""

from __future__ import annotations

import os

from datasets import Dataset
from langchain_google_genai import ChatGoogleGenerativeAI
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import answer_relevancy, context_precision, context_recall, faithfulness
from sentence_transformers import SentenceTransformer

from src.config import CONFIG


class _STEmbeddingsAdapter:
    """Minimal LangChain-Embeddings-compatible adapter around our local
    sentence-transformers model, so RAGAS's answer_relevancy metric (which
    needs an embedder) reuses the SAME embedding model as retrieval,
    avoiding an extra external dependency."""

    def __init__(self, model_name: str):
        self._model = SentenceTransformer(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self._model.encode([text], normalize_embeddings=True).tolist()[0]


def compute_ragas_metrics(records: list[dict]) -> dict:
    """
    records: list of dicts with keys:
        question, answer, contexts (list[str]), ground_truth
    Returns a dict of metric_name -> float (dataset-level mean).
    """
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("GEMINI_API_KEY must be set to run RAGAS evaluation (judge model).")

    dataset = Dataset.from_list(
        [
            {
                "question": r["question"],
                "answer": r["answer"],
                "contexts": r["contexts"],
                "ground_truth": r["ground_truth"],
            }
            for r in records
        ]
    )

    judge_model_name = CONFIG.get("evaluation.judge_model", "gemini-3.5-flash")
    judge_llm = LangchainLLMWrapper(
        ChatGoogleGenerativeAI(model=judge_model_name, temperature=0.0)
    )
    embed_model_name = CONFIG.get("embedding.model_name", "BAAI/bge-small-en-v1.5")
    judge_embeddings = LangchainEmbeddingsWrapper(_STEmbeddingsAdapter(embed_model_name))

    result = evaluate(
        dataset,
        metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
        llm=judge_llm,
        embeddings=judge_embeddings,
    )
    df = result.to_pandas()
    summary = {
        "context_precision": float(df["context_precision"].mean()),
        "context_recall": float(df["context_recall"].mean()),
        "faithfulness": float(df["faithfulness"].mean()),
        "answer_relevancy": float(df["answer_relevancy"].mean()),
        "n_examples": len(df),
    }
    return summary, df
