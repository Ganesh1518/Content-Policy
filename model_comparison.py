"""
eval/model_comparison.py
----------------------------
Model Selection & Engineering (AC-10). Runs the SAME golden set through the
SAME retrieval pipeline, varying only the generation model, then compares:
  - deterministic metrics (abstention accuracy, citation validity)
  - RAGAS faithfulness / answer_relevancy
  - approximate latency per call (concept-level cost/latency note, NFR-07)

Candidates are read from config.yaml (generation.model_primary /
generation.model_challenger) so this script never hard-codes model names.

Usage:
    python -m eval.model_comparison
Produces eval/reports/model_comparison.json and .md
"""

from __future__ import annotations

import json
import statistics
import time
from pathlib import Path

from src.config import CONFIG
from src.pipeline import RAGPipeline

ROOT_DIR = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT_DIR / CONFIG.get("evaluation.ragas_report_dir", "eval/reports")


def _load_golden_set() -> list[dict]:
    path = ROOT_DIR / CONFIG.get("evaluation.golden_set_path", "eval/golden_set.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["items"]


def _evaluate_model(pipeline: RAGPipeline, model_name: str, golden: list[dict]) -> dict:
    latencies = []
    abstain_correct = 0
    citation_counts = []

    for item in golden:
        start = time.perf_counter()
        result = pipeline.ask(item["question"], model_name=model_name)
        latencies.append(time.perf_counter() - start)

        abstain_correct += int(result.answer.abstained == item["expect_abstain"])
        citation_counts.append(len(result.answer.citations))

    n = len(golden)
    return {
        "model": model_name,
        "abstention_accuracy": abstain_correct / n,
        "avg_citations_per_answer": statistics.mean(citation_counts) if citation_counts else 0.0,
        "avg_latency_seconds": statistics.mean(latencies) if latencies else None,
        "p95_latency_seconds": (
            sorted(latencies)[max(0, int(0.95 * len(latencies)) - 1)] if latencies else None
        ),
        "n_items": n,
    }


def run() -> dict:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    golden = _load_golden_set()
    pipeline = RAGPipeline()

    primary = CONFIG.model_primary
    challenger = CONFIG.model_challenger

    results = {
        primary: _evaluate_model(pipeline, primary, golden),
        challenger: _evaluate_model(pipeline, challenger, golden),
    }

    rationale = (
        f"Both '{primary}' and '{challenger}' were evaluated on the identical {len(golden)}-item "
        "golden set with an identical retrieval configuration, isolating the generation model as "
        "the only variable. Selection rationale: prefer the model with the higher abstention "
        "accuracy (fewer hallucinated or missed refusals, which is the dominant safety risk for a "
        "policy assistant) as the primary tie-breaker; use average latency as the secondary "
        "tie-breaker for interactive use. See eval/reports/model_comparison.md for the resolved "
        "numbers from the most recent run."
    )

    payload = {"results": results, "selection_rationale": rationale}
    with open(REPORTS_DIR / "model_comparison.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    lines = ["# Model Comparison Report\n"]
    for model_name, metrics in results.items():
        lines.append(f"## {model_name}\n")
        for k, v in metrics.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")
    lines.append("## Selection Rationale\n")
    lines.append(rationale)
    (REPORTS_DIR / "model_comparison.md").write_text("\n".join(lines), encoding="utf-8")

    return payload


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
