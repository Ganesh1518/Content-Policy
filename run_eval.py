"""
eval/run_eval.py
-------------------
Re-runnable, deterministic evaluation harness (AC-08, AC-09, NFR-06).

Two classes of metric are computed, matching Section 9 of the business case
("Numeric-threshold parameters ... scored deterministically in Python with
no model judgment" vs. metrics that require a judge LLM):

  DETERMINISTIC (pure Python, no model judgment):
    - retrieval_hit_rate:  fraction of golden items whose expected
      (doc_id, clause_id) pair appears among the retrieved chunks.
    - citation_validity_rate: fraction of returned citations whose
      (doc_id, clause_id) pair actually exists in the corpus.
    - abstention_accuracy: fraction of items where `abstained` matches the
      golden `expect_abstain` label.

  MODEL-JUDGED (RAGAS, judge = Gemini):
    - context_precision, context_recall, faithfulness, answer_relevancy.

Outputs (committed evidence per the Evidence-in-Repo Rule):
    eval/reports/eval_run_raw.json       -- every per-question result
    eval/reports/ragas_report.json       -- RAGAS summary metrics
    eval/reports/eval_summary.md         -- human-readable report

Usage:
    python -m eval.run_eval
"""

from __future__ import annotations

import json
from pathlib import Path

from src.config import CONFIG
from src.pipeline import RAGPipeline

ROOT_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT_DIR / CONFIG.get("evaluation.ragas_report_dir", "eval/reports")


def _load_golden_set() -> list[dict]:
    path = ROOT_DIR / CONFIG.get("evaluation.golden_set_path", "eval/golden_set.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["items"]


def _classify_failure(item: dict, retrieved_pairs: set, result) -> str | None:
    """Failure taxonomy: retrieval vs grounding vs synthesis (see
    eval/failure_taxonomy.md for the full definitions)."""
    expected_pairs = {(c["doc_id"], c["clause_id"]) for c in item["expected_context"]}
    if item["expect_abstain"]:
        return None if result.answer.abstained else "grounding_failure_over_answered"

    if result.answer.abstained:
        return "grounding_failure_under_abstained"

    if expected_pairs and not (expected_pairs & retrieved_pairs):
        return "retrieval_failure"

    cited_pairs = {(c.document, c.clause_id) for c in result.answer.citations}
    if expected_pairs and not (expected_pairs & cited_pairs):
        return "synthesis_failure_uncited_context"

    return None


def run() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    golden = _load_golden_set()
    pipeline = RAGPipeline()

    raw_results = []
    hit_count = 0
    citation_checked = 0
    citation_valid = 0
    abstention_correct = 0
    failures = []

    # Build a lookup of every real (doc_id, clause_id) pair for citation validity checks.
    from src.ingestion.loader import load_corpus

    all_clauses = load_corpus(CONFIG.corpus_dir, CONFIG.get("corpus.doc_glob", "*.md"))
    valid_pairs = {(c.doc_id, c.clause_id) for c in all_clauses}
    # also register merged/split clause_ids that may appear as "3.1+3.2" or "3.1::0" fragments
    for c in all_clauses:
        valid_pairs.add((c.doc_id, c.clause_id.split("::")[0]))

    for item in golden:
        result = pipeline.ask(item["question"])
        retrieved_pairs = {
            (c.metadata.get("doc_id"), c.metadata.get("clause_id")) for c in result.retrieved_chunks
        }
        expected_pairs = {(c["doc_id"], c["clause_id"]) for c in item["expected_context"]}

        if expected_pairs:
            hit = bool(expected_pairs & retrieved_pairs)
            hit_count += int(hit)

        for c in result.answer.citations:
            citation_checked += 1
            key = (c.document, c.clause_id)
            if key in valid_pairs or (c.document, c.clause_id.split("+")[0]) in valid_pairs:
                citation_valid += 1

        abstain_match = result.answer.abstained == item["expect_abstain"]
        abstention_correct += int(abstain_match)

        failure = _classify_failure(item, retrieved_pairs, result)
        if failure:
            failures.append({"id": item["id"], "question": item["question"], "failure_type": failure})

        raw_results.append(
            {
                "id": item["id"],
                "question": item["question"],
                "ac_ref": item["ac_ref"],
                "sub_queries": result.sub_queries,
                "retrieved": [
                    {"doc_id": c.metadata.get("doc_id"), "clause_id": c.metadata.get("clause_id"), "score": c.score}
                    for c in result.retrieved_chunks
                ],
                "reference_answer": item["reference_answer"],
                "generated_answer": result.answer.answer,
                "citations": [c.model_dump() for c in result.answer.citations],
                "confidence": result.answer.confidence,
                "grounded": result.answer.grounded,
                "abstained": result.answer.abstained,
                "expect_abstain": item["expect_abstain"],
                "abstain_correct": abstain_match,
                "contexts_for_ragas": [c.text for c in result.retrieved_chunks],
            }
        )

    n = len(golden)
    n_with_expected = sum(1 for i in golden if i["expected_context"])
    deterministic = {
        "retrieval_hit_rate": hit_count / n_with_expected if n_with_expected else None,
        "citation_validity_rate": citation_valid / citation_checked if citation_checked else None,
        "abstention_accuracy": abstention_correct / n,
        "n_items": n,
    }

    with open(REPORTS_DIR / "eval_run_raw.json", "w", encoding="utf-8") as f:
        json.dump({"deterministic_metrics": deterministic, "failures": failures, "results": raw_results}, f, indent=2)

    # ---- RAGAS (model-judged) metrics -------------------------------------------------
    ragas_summary = None
    try:
        from eval.ragas_metrics import compute_ragas_metrics

        ragas_records = [
            {
                "question": r["question"],
                "answer": r["generated_answer"],
                "contexts": r["contexts_for_ragas"] or ["(no context retrieved)"],
                "ground_truth": r["reference_answer"],
            }
            for r in raw_results
        ]
        ragas_summary, _df = compute_ragas_metrics(ragas_records)
        with open(REPORTS_DIR / "ragas_report.json", "w", encoding="utf-8") as f:
            json.dump(ragas_summary, f, indent=2)
    except Exception as e:  # pragma: no cover - requires a live API key
        ragas_summary = {"error": str(e)}
        with open(REPORTS_DIR / "ragas_report.json", "w", encoding="utf-8") as f:
            json.dump(ragas_summary, f, indent=2)

    _write_markdown_summary(deterministic, ragas_summary, failures)
    return {"deterministic": deterministic, "ragas": ragas_summary, "failures": failures}


def _write_markdown_summary(deterministic: dict, ragas_summary: dict, failures: list[dict]):
    lines = ["# Evaluation Summary\n"]
    lines.append("## Deterministic metrics (Python, no model judgment)\n")
    for k, v in deterministic.items():
        lines.append(f"- **{k}**: {v}")
    lines.append("\n## RAGAS metrics (judge = Gemini)\n")
    if ragas_summary:
        for k, v in ragas_summary.items():
            lines.append(f"- **{k}**: {v}")
    lines.append(f"\n## Failure taxonomy ({len(failures)} flagged items)\n")
    for f in failures:
        lines.append(f"- `{f['id']}` [{f['failure_type']}]: {f['question']}")
    (REPORTS_DIR / "eval_summary.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    summary = run()
    print(json.dumps(summary, indent=2, default=str))
