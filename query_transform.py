"""
src/retrieval/query_transform.py
------------------------------------
Query transformation stage (AC-07). Multi-part or ambiguous questions are
rewritten/expanded/decomposed BEFORE retrieval so each sub-question can pull
its own relevant clause(s). Falls back to the original query unchanged if the
LLM call fails or the API key is not configured (graceful degradation, NFR-05)
so retrieval still works even without transformation.
"""

from __future__ import annotations

import json
import re

from src.config import CONFIG
from src.llm.gemini_client import GeminiClient, GeminiUnavailableError

_MULTI_PART_HINTS = re.compile(r"\b(and|,|\?.*\?)\b", re.IGNORECASE)

_PROMPT = """You transform a user question into a small set of focused search \
queries for a hospital-policy retrieval system. Rules:
- If the question is a single, clear ask, return it unchanged as the only query.
- If it has multiple parts (e.g., "what is X and who is responsible for Y"), \
decompose it into separate sub-queries, one per part.
- If it is vague, rewrite it into a more specific query using policy/SOP \
terminology (e.g., "protocol", "SOP", "responsible role", "timeline").
- Return at most {max_sub} queries.
- Respond ONLY with a JSON array of strings, no prose.

Question: {question}
"""


def transform_query(question: str) -> list[str]:
    if not CONFIG.get("query_transformation.enabled", True):
        return [question]

    max_sub = CONFIG.get("query_transformation.max_sub_queries", 3)

    # Cheap heuristic gate: skip the LLM call entirely for obviously simple,
    # single-clause questions to save latency and cost.
    if not _MULTI_PART_HINTS.search(question) and len(question.split()) <= 14:
        return [question]

    try:
        client = GeminiClient(model_name=CONFIG.model_primary)
        raw = client.generate(_PROMPT.format(max_sub=max_sub, question=question))
        cleaned = raw.strip().strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
        queries = json.loads(cleaned)
        queries = [q.strip() for q in queries if isinstance(q, str) and q.strip()]
        return queries[:max_sub] if queries else [question]
    except (GeminiUnavailableError, json.JSONDecodeError, Exception):
        # Graceful fallback: never let query transformation block retrieval.
        return [question]
