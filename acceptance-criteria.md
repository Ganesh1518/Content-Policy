# Acceptance Criteria (AC-01 .. AC-10)

Per the **AC-Traceability Rule**, every criterion below is referenced by at
least one test in `tests/test_pipeline.py` or one eval-set entry in
`eval/golden_set.json` carrying its `AC-NN` identifier.

| ID | Criterion | Traced by |
|---|---|---|
| AC-01 | Ingests a synthetic corpus of ≥30 documents into a persisted vector index; ingestion is re-runnable and idempotent. | `tests/test_pipeline.py::test_ac01_corpus_and_idempotent_ingest` |
| AC-02 | A user can ask a natural-language question and receive an answer grounded only in the corpus, with ≥1 clause-level citation per answer. | `eval/golden_set.json` items `G-01`..`G-20`; `tests/test_pipeline.py::test_ac02_citations_present` |
| AC-03 | Retrieval combines lexical (BM25) and semantic search and fuses the two result sets via Reciprocal Rank Fusion before generation. | `tests/test_pipeline.py::test_ac03_hybrid_fusion` |
| AC-04 | Retrieved candidates are reranked (cross-encoder) before the top-K is passed to the generator. | `tests/test_pipeline.py::test_ac04_reranking_reduces_candidates` |
| AC-05 | When the corpus does not support an answer, the system abstains or flags low confidence rather than fabricating. | `eval/golden_set.json` items `G-21`, `G-22`; `tests/test_pipeline.py::test_ac05_abstention` |
| AC-06 | Answers are returned as a validated structured object (Pydantic/JSON schema) containing answer text, citations, applicable policy/SOP, step sequence, responsible role, and a grounding/confidence indicator. | `src/generation/schema.py::AnswerResponse`; `tests/test_pipeline.py::test_ac06_structured_schema` |
| AC-07 | Multi-part or ambiguous queries are transformed (rewrite/expansion/decomposition) before retrieval. | `eval/golden_set.json` item `G-20`; `tests/test_pipeline.py::test_ac07_query_transformation` |
| AC-08 | A golden evaluation set of ≥20 questions with reference answers/expected contexts is committed with a re-runnable scoring script. | `eval/golden_set.json` (22 items); `eval/run_eval.py` |
| AC-09 | RAGAS metrics (context precision, context recall, faithfulness, answer relevancy) are computed and the numeric results committed as a report artifact. | `eval/run_eval.py` → `eval/reports/ragas_report.json` |
| AC-10 | At least two candidate LLMs are evaluated on the custom eval set and a comparison (metrics + selection rationale) is committed. | `eval/model_comparison.py` → `eval/reports/model_comparison.json` |

## Non-Functional Requirements (NFR-01 .. NFR-08) — traceability

| ID | Requirement | Traced by |
|---|---|---|
| NFR-01 | No secrets committed; config via env vars + `.env.example`. | `.env.example`, `.gitignore`, `src/config.py` |
| NFR-02 | Pipeline + evaluation run end-to-end from a single documented command. | `README.md` Quick Start; `scripts/run_all.sh` |
| NFR-03 | All data synthetic; no PII written to logs in plaintext. | `data/corpus/*` (frontmatter-only synthetic fields); `config.yaml: logging.redact_pii` |
| NFR-04 | Retrieval parameters externalized in config, not hard-coded. | `config/config.yaml` |
| NFR-05 | Provider calls implement retries and fail gracefully. | `src/llm/gemini_client.py` (`tenacity` retry); `src/generation/generator.py` fallback to refusal |
| NFR-06 | Every quality claim reproducible — eval script + dataset committed. | `eval/run_eval.py`, `eval/golden_set.json` |
| NFR-07 | Cost/latency addressed at concept level. | `docs/cost-latency-note.md`; `eval/model_comparison.py` latency fields |
| NFR-08 | Basic logging in place; no answer returned without provenance above the abstention threshold. | `src/generation/generator.py::_code_level_abstention_check`; `logging.basicConfig` in `src/pipeline.py` |
