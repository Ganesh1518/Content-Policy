# Failure Taxonomy — Retrieval vs. Grounding vs. Synthesis

This taxonomy is applied automatically by `eval/run_eval.py` (function
`_classify_failure`) against every golden-set item, and is written to
`eval/reports/eval_run_raw.json` / `eval_summary.md` on each run.

| Category | Definition | Detection rule (deterministic) |
|---|---|---|
| **retrieval_failure** | The correct clause exists in the corpus, but none of the retrieved (post-rerank) chunks match the golden `expected_context` pair. The pipeline never gave the generator a chance to answer correctly. | `expected_context` pairs ∩ retrieved `(doc_id, clause_id)` pairs = ∅ |
| **grounding_failure_under_abstained** | The correct clause WAS retrieved, but the pipeline abstained anyway (over-cautious). | `abstained == True` while `expect_abstain == False` |
| **grounding_failure_over_answered** | The question is genuinely out of scope (golden `expect_abstain == True`), but the pipeline produced a confident, non-abstaining answer — the highest-severity failure class for this assistant, since it risks fabrication. | `abstained == False` while `expect_abstain == True` |
| **synthesis_failure_uncited_context** | The correct clause was retrieved and the pipeline did not abstain, but the generated answer's citations do not include the expected `(doc_id, clause_id)` pair — i.e., retrieval succeeded but generation cited the wrong or no clause. | expected pair retrieved, not abstained, but expected pair ∉ cited pairs |

## Why this split matters

- A **retrieval_failure** is fixed by tuning chunking, embeddings, BM25
  weighting, or the fusion/rerank stage.
- A **grounding_failure** (either direction) is fixed by tuning the
  abstention threshold (`config.yaml: abstention.min_reranker_score`) or the
  grounding prompt's confidence calibration instructions.
- A **synthesis_failure** is fixed by tuning the generation prompt's
  citation instructions or the structured-output schema/validation.

Splitting failures this way avoids the common anti-pattern of tuning the
generator when the real defect is upstream in retrieval (or vice versa).

## How to read a report

Run:
```
python -m eval.run_eval
```
Then open `eval/reports/eval_summary.md`. Each flagged item lists its
`failure_type`. A healthy pipeline should show zero
`grounding_failure_over_answered` items — that is the safety-critical class
and is weighted accordingly when interpreting results.
