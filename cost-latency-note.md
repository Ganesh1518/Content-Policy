# Cost / Latency Note (Concept Level)

Per NFR-07, this is a concept-level estimate for a representative query, not
a benchmarking or performance-governance exercise.

## Representative query
"What is the hand-hygiene protocol before a procedure, and who audits
compliance with it?" (golden set item `G-20`; a moderately complex,
two-part question that exercises query decomposition.)

## Cost, per call

| Stage | Approx. tokens | Notes |
|---|---|---|
| Query transformation (Gemini call) | ~150 input / ~40 output | Only triggered for multi-part/ambiguous questions; simple single-clause questions skip this call entirely (`query_transform.py` heuristic gate). |
| Embedding (local, sentence-transformers) | n/a — CPU-local | No API cost; amortized ingestion-time cost only. |
| Reranking (local cross-encoder) | n/a — CPU-local | No API cost. |
| Generation (Gemini call, structured JSON) | ~900–1200 input (prompt + up to 5 context chunks) / ~250–400 output | Dominant cost driver. |

At current (Aug 2026) Gemini Flash-tier public pricing on the order of
low-single-digit dollars per million input tokens and mid-single-digit
dollars per million output tokens, a single representative query — one
query-transformation call plus one generation call — costs a small fraction
of a cent. Exact pricing should be checked against Google's current published
rate card at request time, since Gemini pricing tiers change over the model
lifecycle (see `ai.google.dev` release notes).

## Latency, per call (approximate, network-dependent)

| Stage | Approx. latency |
|---|---|
| Query transformation (Gemini, conditional) | 0.3 – 0.8 s |
| Hybrid retrieval (BM25 + vector, local) | < 0.05 s |
| Reranking (local cross-encoder, ≤20 candidates) | 0.1 – 0.3 s |
| Generation (Gemini, structured JSON) | 0.8 – 2.0 s |
| **End-to-end (typical)** | **~1.2 – 3.2 s** |

`eval/model_comparison.py` records `avg_latency_seconds` and
`p95_latency_seconds` empirically for each candidate model on every run,
so these figures are always reproducible against the live API rather than
taken only from this note.
