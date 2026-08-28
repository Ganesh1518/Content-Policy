# Embedding Model Selection & Chunking Strategy Rationale

## Embedding Model

**Selected:** `BAAI/bge-small-en-v1.5` (Sentence-Transformers, local, open source)

| Candidate | MTEB retrieval avg (public leaderboard, approx.) | Dimensions | Notes |
|---|---|---|---|
| `BAAI/bge-small-en-v1.5` | ~51–52 | 384 | Strong retrieval score-to-size ratio; runs comfortably on CPU with no GPU dependency, matching the project's pip-only / no-Docker constraint. |
| `intfloat/e5-base-v2` | ~50–51 | 768 | Comparable quality, 2x the vector size and index footprint for no measurable retrieval gain on a corpus this size (~30 documents). |
| `sentence-transformers/all-MiniLM-L6-v2` | ~45 | 384 | Fastest and smallest, but noticeably weaker on instruction/asymmetric retrieval benchmarks, which matters because policy questions ("what is the protocol for...") are phrased differently than the clause text they must match. |

**Rationale:**
1. **Dimensionality / cost trade-off.** At 384 dimensions, `bge-small-en-v1.5`
   keeps the Chroma index small and query latency low, appropriate for a
   corpus of ~30 documents / a few hundred chunks — `e5-base-v2`'s extra 768
   dimensions would double storage and query cost with negligible quality
   gain at this corpus scale.
2. **MTEB-informed quality.** Among small (≤400-dim) open models, BGE-small
   consistently ranks near the top of the MTEB retrieval subset, ahead of
   MiniLM-class models, which matters here because clause text and natural-
   language questions rarely share exact vocabulary (asymmetric retrieval).
3. **License and locality.** MIT-licensed, runs fully local via
   `sentence-transformers`, satisfying the Open-Source & No-Docker Rule with
   no external embedding API call (no added latency, no additional secret
   to manage).
4. **Normalization.** Embeddings are L2-normalized (`embedding.normalize:
   true` in config) so cosine similarity and the reranker's downstream
   [0, 1] score scale stay consistent for the abstention threshold.

## Chunking Strategy Rationale

**Selected: clause-aware recursive split with sentence-window overlap**
(implemented in `src/ingestion/chunker.py`).

Naive fixed-size chunking was rejected because the corpus is already
authored in short, numbered, legally meaningful clauses (`Section N.M`).
Fixed-size windows would routinely straddle a clause boundary and separate
an obligation from the role or timeline that qualifies it — directly
undermining clause-level citation accuracy (AC-02) and RAGAS faithfulness.

Instead:
1. Each clause is the default chunking unit — it already respects the
   author's semantic and legal boundaries.
2. Clauses longer than `chunking.max_chars` (900) are recursively split on
   sentence boundaries only (never mid-sentence), with a
   `chunking.overlap_chars` (150) character tail carried into the next
   piece so a split clause's qualifying condition stays visible to the
   reranker/generator.
3. Clauses shorter than `chunking.min_chars` (120) are merged forward with
   the next clause in the same document to avoid indexing low-signal
   fragments.

All chunk-level parameters are externalized in `config/config.yaml` under
`chunking:` (NFR-04) — nothing is hard-coded in `src/ingestion/chunker.py`.
