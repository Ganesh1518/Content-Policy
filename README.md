# Hospital Policy & SOP Assistant — Retrieval-Augmented Assistant

Business Case `AAIE_011_HLC` · Domain: Healthcare — Hospital Operations & Compliance
Track: Gen AI Core + RAG Engineering

A production-grade, measurable RAG pipeline over a **synthetic** hospital
policy/SOP corpus: hybrid retrieval (BM25 + semantic + RRF fusion), cross-
encoder reranking, grounded generation with clause-level citations,
validated structured output, abstention, and a RAGAS-based evaluation
harness with a two-model comparison. See `specs/acceptance-criteria.md` for
full AC-01..AC-10 / NFR-01..NFR-08 traceability.

## Quick Start (single command, NFR-02)

```bash
cp .env.example .env
# edit .env and set GEMINI_API_KEY

bash scripts/run_all.sh
```

This installs dependencies, generates the synthetic corpus, ingests it
(chunk → embed → persist, idempotent), runs the golden-set evaluation
(RAGAS + deterministic metrics), and runs the two-model comparison —
writing all committed evidence to `eval/reports/`.

### Manual step-by-step (equivalent)

```bash
pip install -r requirements.txt

python scripts/generate_corpus.py          # writes 30 docs to data/corpus/
python -m src.ingestion.ingest              # chunk -> embed -> Chroma + BM25

python -m src.pipeline "What is the hand-hygiene protocol before a procedure?"
python -m interface.cli "What is the two-identifier rule for patient identification?"
streamlit run interface/app.py              # optional lightweight UI

python -m eval.run_eval                     # RAGAS + deterministic metrics
python -m eval.model_comparison             # two-LLM comparison

pytest tests/ -q                            # offline-safe subset runs without an API key
```

## Repository Layout

```
config/config.yaml           Externalized chunking/retrieval/model config (NFR-04)
data/corpus/                 30 synthetic hospital policy/SOP documents (AC-01)
docs/business-case.md        Problem, users, corpus, guardrails, success metrics
docs/embedding-selection.md  MTEB-informed embedding + chunking rationale
docs/cost-latency-note.md    Concept-level cost/latency note (NFR-07)
docs/sample-outputs.md       Committed sample outputs incl. refusal example
specs/acceptance-criteria.md AC-01..AC-10 / NFR-01..NFR-08 traceability table
src/ingestion/                Loader, clause-aware chunker, idempotent ingest
src/retrieval/                BM25, vector, RRF fusion, cross-encoder reranker,
                               query transformation
src/generation/               Pydantic schema, grounding prompt, generator
src/llm/gemini_client.py      Gemini wrapper with retries (NFR-05)
src/pipeline.py               End-to-end orchestrator + CLI entrypoint
interface/                    CLI and optional Streamlit UI
eval/golden_set.json          22-question golden evaluation set (AC-08)
eval/run_eval.py              RAGAS + deterministic metrics + failure taxonomy
eval/model_comparison.py      Two-candidate-LLM comparison (AC-10)
eval/failure_taxonomy.md      Retrieval vs grounding vs synthesis failure definitions
tests/test_pipeline.py        Tests mapped to AC-NN identifiers
scripts/generate_corpus.py    Synthetic corpus generator
scripts/run_all.sh            Single documented end-to-end command
```

## Technology Stack (fixed, Section 4 of the business case)

| Layer | Tool |
|---|---|
| Language / Orchestration | Python 3.11+ |
| LLM Provider | Google Gemini API only |
| Embeddings | Sentence-Transformers `BAAI/bge-small-en-v1.5` (local) |
| Vector Store | Chroma (persisted, in-process, no Docker) |
| Lexical / Hybrid | `rank_bm25` fused with vector search via RRF |
| Reranker | Sentence-Transformers CrossEncoder `ms-marco-MiniLM-L-6-v2` |
| Evaluation | RAGAS, judge = Gemini |
| Interface | CLI (mandatory-adjacent) + optional Streamlit |

No Docker, no external database service — everything runs via `pip` +
Python locally, per the Open-Source & No-Docker Rule.

## Configuration & Secrets (NFR-01)

All parameters live in `config/config.yaml`. The only required secret is
`GEMINI_API_KEY`, read from `.env` (see `.env.example`); `.env` itself is
git-ignored and nothing is hard-coded in source.

## Notes on Model Names

`config/config.yaml: generation.model_primary / model_challenger` currently
point at `gemini-3.5-flash` and `gemini-3.5-flash-lite`. Gemini model
identifiers are periodically deprecated by Google; if either name has been
retired by the time you run this, update the two config values (or the
`GEMINI_MODEL_PRIMARY` / `GEMINI_MODEL_CHALLENGER` env overrides) to the
current generally-available Flash-tier model IDs at
`ai.google.dev/gemini-api/docs/models` — no code changes are required.

## What Is Evaluated vs. Not (Section 2 of the business case)

**Evaluated:** retrieval-pipeline engineering (chunking, hybrid search,
fusion, reranking, query transformation), grounded generation with
clause-level citations, structured output, measured retrieval quality
(RAGAS on the committed golden set), model/embedding selection, and
engineering reproducibility.

**Not evaluated:** visual polish of the interface, model fine-tuning, or
which library is picked within the approved open-source set.
