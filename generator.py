"""
src/generation/generator.py
------------------------------
Generation & grounding layer (Section 7.4 of the business case). Calls
Gemini with the grounding prompt + structured JSON schema, validates the
result against the Pydantic model, and enforces the abstention rule (AC-05)
independently of what the model claims, using the retrieval score threshold
from config as a second, code-level guardrail.
"""

from __future__ import annotations

import json
import logging

from src.config import CONFIG
from src.generation.prompt import build_prompt
from src.generation.schema import GEMINI_JSON_SCHEMA, REFUSAL_EXAMPLE, AnswerResponse
from src.llm.gemini_client import GeminiClient, GeminiUnavailableError
from src.retrieval.types import RetrievedChunk

logger = logging.getLogger(__name__)


def _code_level_abstention_check(chunks: list[RetrievedChunk]) -> bool:
    """Second, deterministic guardrail (NFR-08): never let a low-evidence
    retrieval reach the generator claiming groundedness. Returns True if the
    pipeline should abstain outright without calling the LLM."""
    if not chunks:
        return True
    min_score = CONFIG.get("abstention.min_reranker_score", 0.15)
    return max(c.score for c in chunks) < min_score


def generate_answer(
    question: str,
    chunks: list[RetrievedChunk],
    model_name: str | None = None,
) -> AnswerResponse:
    if _code_level_abstention_check(chunks):
        logger.info("Abstaining: retrieval evidence below threshold for question=%r", question)
        return REFUSAL_EXAMPLE.model_copy(update={"answer": REFUSAL_EXAMPLE.answer})

    prompt = build_prompt(question, chunks)
    client = GeminiClient(model_name=model_name or CONFIG.model_primary)

    try:
        raw = client.generate(prompt, response_schema=GEMINI_JSON_SCHEMA)
        payload = json.loads(raw)
        response = AnswerResponse.model_validate(payload)
    except GeminiUnavailableError:
        logger.warning("Gemini unavailable; returning safe fallback refusal.")
        return REFUSAL_EXAMPLE
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("Model returned invalid structured output (%s); abstaining.", e)
        return REFUSAL_EXAMPLE

    # Enforce AC-05/NFR-08 regardless of what the model self-reported: a
    # grounded=True answer with zero citations is not allowed to pass.
    min_citations = CONFIG.get("abstention.min_citations_required", 1)
    if response.grounded and len(response.citations) < min_citations:
        logger.info("Model claimed grounded but returned no citations; overriding to abstain.")
        return REFUSAL_EXAMPLE

    return response
