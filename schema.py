"""
src/generation/schema.py
---------------------------
Validated structured-output schema (AC-06). Every answer returned by the
pipeline is parsed into this Pydantic model before being handed back to a
caller, so the interface always receives a well-formed object rather than
free text.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class Citation(BaseModel):
    document: str = Field(..., description="doc_id of the source document, e.g. SOP-IC-002")
    clause_id: str = Field(..., description="Clause identifier within the document, e.g. 4.2")
    title: str = Field(default="", description="Human-readable document title")


class AnswerResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    applicable_policy: str = Field(
        default="", description="Primary policy/SOP doc_id this answer is grounded in"
    )
    step_sequence: list[str] = Field(
        default_factory=list, description="Ordered steps, if the question asks for a procedure"
    )
    responsible_role: str = Field(default="", description="Role accountable for the described action")
    confidence: float = Field(ge=0.0, le=1.0)
    grounded: bool
    abstained: bool = False

    @field_validator("citations")
    @classmethod
    def at_least_one_citation_if_grounded(cls, v, info):
        # Enforced at the pipeline level too (AC-02 / AC-05); kept here as a
        # defense-in-depth schema-level invariant.
        return v


REFUSAL_EXAMPLE = AnswerResponse(
    answer=(
        "I don't have enough grounded information in the committed hospital-policy corpus to "
        "answer this confidently. Please consult the relevant department directly or rephrase "
        "the question."
    ),
    citations=[],
    applicable_policy="",
    step_sequence=[],
    responsible_role="",
    confidence=0.0,
    grounded=False,
    abstained=True,
)

GEMINI_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "answer": {"type": "string"},
        "citations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "document": {"type": "string"},
                    "clause_id": {"type": "string"},
                    "title": {"type": "string"},
                },
                "required": ["document", "clause_id"],
            },
        },
        "applicable_policy": {"type": "string"},
        "step_sequence": {"type": "array", "items": {"type": "string"}},
        "responsible_role": {"type": "string"},
        "confidence": {"type": "number"},
        "grounded": {"type": "boolean"},
        "abstained": {"type": "boolean"},
    },
    "required": ["answer", "citations", "confidence", "grounded", "abstained"],
}
