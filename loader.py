"""
src/ingestion/loader.py
------------------------
Parses each corpus markdown file (YAML frontmatter + numbered `## <clause_id>
<heading>` sections) into a list of ClauseRecord objects. This preserves the
document's native clause structure so the chunker can attach a stable
`clause_id` to every chunk (required for clause-level citation, AC-02).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ClauseRecord:
    doc_id: str
    doc_type: str
    title: str
    owner_role: str
    effective_date: str
    clause_id: str
    heading: str
    text: str
    source_path: str


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n\n(.*)$", re.DOTALL)
CLAUSE_RE = re.compile(r"^##\s+(\S+)\s+(.*)$")


def _split_frontmatter(raw: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError("Corpus document is missing required YAML frontmatter.")
    meta = yaml.safe_load(m.group(1))
    body = m.group(2)
    return meta, body


def _split_clauses(body: str) -> list[tuple[str, str, str]]:
    """Returns list of (clause_id, heading, text) using '## <id> <heading>' markers."""
    lines = body.splitlines()
    clauses: list[tuple[str, str, str]] = []
    current_id, current_heading, buf = None, None, []

    def flush():
        if current_id is not None:
            text = "\n".join(buf).strip()
            if text:
                clauses.append((current_id, current_heading, text))

    for line in lines:
        m = CLAUSE_RE.match(line.strip())
        if m:
            flush()
            current_id, current_heading = m.group(1), m.group(2)
            buf = []
        elif line.startswith("# "):
            continue  # document title line, not a clause
        else:
            buf.append(line)
    flush()
    return clauses


def load_corpus(corpus_dir: Path, doc_glob: str = "*.md") -> list[ClauseRecord]:
    records: list[ClauseRecord] = []
    files = sorted(Path(corpus_dir).glob(doc_glob))
    if not files:
        raise FileNotFoundError(
            f"No corpus files matching {doc_glob} found under {corpus_dir}. "
            "Run `python scripts/generate_corpus.py` first."
        )
    for fp in files:
        raw = fp.read_text(encoding="utf-8")
        meta, body = _split_frontmatter(raw)
        for clause_id, heading, text in _split_clauses(body):
            records.append(
                ClauseRecord(
                    doc_id=meta["doc_id"],
                    doc_type=meta["doc_type"],
                    title=meta["title"],
                    owner_role=meta.get("owner_role", ""),
                    effective_date=str(meta.get("effective_date", "")),
                    clause_id=clause_id,
                    heading=heading,
                    text=text,
                    source_path=str(fp),
                )
            )
    return records
