"""
src/generation/prompt.py
---------------------------
Grounding prompt (AC-02, AC-05, AC-06). The prompt forces the model to:
  1. Answer ONLY from the supplied context chunks (no outside knowledge).
  2. Cite every claim with a (document, clause_id) pair drawn from the
     context metadata actually provided.
  3. Abstain (grounded=false, abstained=true) when the context does not
     support a confident answer, rather than fabricating one.
  4. Return the applicable policy/SOP, any step sequence, and the
     responsible role when the question concerns a procedure.
"""

from __future__ import annotations

SYSTEM_INSTRUCTIONS = """You are a grounded hospital-policy and SOP assistant. \
You answer ONLY using the CONTEXT provided below, which was retrieved from a \
synthetic hospital-policy corpus. You must never use outside knowledge, and \
you must never give legal or financial advice beyond quoting the policy text \
itself (Grounding & Advice Rule).

Rules:
1. Every factual claim in `answer` must be traceable to at least one context \
chunk. Populate `citations` with the exact `document` (doc_id) and \
`clause_id` values shown in the context — never invent an id.
2. If the question asks about a procedure, populate `step_sequence` with the \
ordered steps drawn from the context, and `responsible_role` with the role \
named in the context.
3. If the context does not contain enough information to answer confidently, \
set `grounded=false`, `abstained=true`, leave `citations` empty, set \
`confidence` below 0.3, and write a short refusal in `answer` directing the \
user to consult the relevant department. Do NOT guess.
4. `confidence` reflects how directly the context supports the answer: 1.0 = \
explicit, unambiguous support; 0.0 = no support.
5. Output must be a single JSON object matching the provided schema, nothing else.
"""

USER_TEMPLATE = """CONTEXT (retrieved clauses, do not exceed this information):
{context_block}

QUESTION:
{question}

Respond with the JSON object only.
"""


def format_context_block(chunks: list) -> str:
    lines = []
    for c in chunks:
        meta = c.metadata
        lines.append(
            f"[document={meta.get('doc_id')} clause_id={meta.get('clause_id')} "
            f"title=\"{meta.get('title')}\" owner_role=\"{meta.get('owner_role')}\"]\n{c.text}"
        )
    return "\n\n".join(lines) if lines else "(no context retrieved)"


def build_prompt(question: str, chunks: list) -> str:
    context_block = format_context_block(chunks)
    return SYSTEM_INSTRUCTIONS + "\n\n" + USER_TEMPLATE.format(
        context_block=context_block, question=question
    )
