#!/usr/bin/env bash
# scripts/run_all.sh
# Single documented command required by NFR-02:
#   "Pipeline and evaluation run end-to-end from a single documented command
#    with committed sample data and a README quick-start."
#
# Usage:
#   bash scripts/run_all.sh
set -euo pipefail

echo "== 1/5 Installing dependencies =="
pip install -r requirements.txt --quiet

echo "== 2/5 Generating synthetic corpus (>=30 docs) =="
python scripts/generate_corpus.py

echo "== 3/5 Ingesting corpus (chunk -> embed -> persist, idempotent) =="
python -m src.ingestion.ingest

echo "== 4/5 Running golden-set evaluation (RAGAS + deterministic metrics) =="
python -m eval.run_eval

echo "== 5/5 Running two-model comparison =="
python -m eval.model_comparison

echo ""
echo "Done. See eval/reports/ for committed evidence:"
echo "  - eval_run_raw.json / eval_summary.md"
echo "  - ragas_report.json"
echo "  - model_comparison.json / model_comparison.md"
echo ""
echo "Try a single question: python -m src.pipeline \"What is the hand-hygiene protocol before a procedure?\""
