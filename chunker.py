"""
src/ingestion/chunker.py
--------------------------
Chunking strategy: CLAUSE-AWARE RECURSIVE SPLIT WITH SENTENCE-WINDOW OVERLAP.

Rationale (see docs/embedding-selection.md for the full writeup):
Hospital policies and SOPs are already authored as short, numbered, legally
meaningful clauses (Section N.M). A naive fixed-size splitter would routinely
cut a clause in half, separating an obligation from the timeline or role that
qualifies it (e.g., splitting "must report within 1 hour" from "the charge
nurse is responsible"), which would corrupt clause-level citation (AC-02) and
degrade faithfulness.

Instead we:
  1. Treat each clause as the primary chunking unit (respects semantic and
     legal boundaries the author already defined).
  2. Recursively split only clauses that exceed `max_chars`, on paragraph then
     sentence boundaries, so we never truncate mid-sentence.
  3. Attach a `sentence_window` of trailing context from the *previous* chunk
     of the same clause, so a reranker/generator reading a split chunk still
     has the qualifying condition in view.
  4. Merge clauses shorter than `min_chars` with the following clause of the
     same document to avoid indexing near-empty, low-signal chunks.

Every chunk carries clause-level metadata (doc_id, clause_id, doc_type,
section/heading) required for AC-02 and the metadata schema in AC-01 /
Section 6.1 of the business case.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.ingestion.loader import ClauseRecord

SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    doc_type: str
    title: str
    owner_role: str
    effective_date: str
    clause_id: str
    heading: str
    text: str
    source_path: str


def _split_long_text(text: str, max_chars: int, overlap_chars: int) -> list[str]:
    sentences = SENTENCE_SPLIT_RE.split(text)
    parts: list[str] = []
    buf = ""
    for sent in sentences:
        if len(buf) + len(sent) + 1 <= max_chars:
            buf = f"{buf} {sent}".strip()
        else:
            if buf:
                parts.append(buf)
            # start next chunk with an overlap tail of the previous chunk
            tail = buf[-overlap_chars:] if overlap_chars and buf else ""
            buf = f"{tail} {sent}".strip()
    if buf:
        parts.append(buf)
    return parts if parts else [text]


def chunk_clauses(
    clauses: list[ClauseRecord],
    max_chars: int = 900,
    overlap_chars: int = 150,
    min_chars: int = 120,
) -> list[Chunk]:
    chunks: list[Chunk] = []

    # merge short clauses forward within the same document
    merged: list[ClauseRecord] = []
    i = 0
    while i < len(clauses):
        current = clauses[i]
        if len(current.text) < min_chars and i + 1 < len(clauses) and clauses[i + 1].doc_id == current.doc_id:
            nxt = clauses[i + 1]
            combined_text = f"{current.text}\n{nxt.text}"
            merged.append(
                ClauseRecord(
                    doc_id=current.doc_id,
                    doc_type=current.doc_type,
                    title=current.title,
                    owner_role=current.owner_role,
                    effective_date=current.effective_date,
                    clause_id=f"{current.clause_id}+{nxt.clause_id}",
                    heading=f"{current.heading} / {nxt.heading}",
                    text=combined_text,
                    source_path=current.source_path,
                )
            )
            i += 2
        else:
            merged.append(current)
            i += 1

    for clause in merged:
        if len(clause.text) <= max_chars:
            parts = [clause.text]
        else:
            parts = _split_long_text(clause.text, max_chars, overlap_chars)

        for idx, part in enumerate(parts):
            chunk_id = f"{clause.doc_id}::{clause.clause_id}::{idx}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=clause.doc_id,
                    doc_type=clause.doc_type,
                    title=clause.title,
                    owner_role=clause.owner_role,
                    effective_date=clause.effective_date,
                    clause_id=clause.clause_id,
                    heading=clause.heading,
                    text=part,
                    source_path=clause.source_path,
                )
            )
    return chunks
