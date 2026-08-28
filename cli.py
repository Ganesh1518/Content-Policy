"""
interface/cli.py
-------------------
Minimal CLI interface (Section 6.1: "A minimal interface (CLI / Streamlit /
Gradio / FastAPI) to exercise the pipeline"). Interface visual polish is
explicitly out of scope (Section 6.2); this is a thin, functional wrapper.

Usage:
    python -m interface.cli "What is the hand-hygiene protocol before a procedure?"
"""

from __future__ import annotations

import sys

from src.pipeline import RAGPipeline


def main():
    if len(sys.argv) < 2:
        print('Usage: python -m interface.cli "<question>"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    pipeline = RAGPipeline()
    result = pipeline.ask(question)

    print(f"\nQ: {result.question}\n")
    if result.answer.abstained:
        print("[ABSTAINED — insufficient grounded evidence]")
    print(result.answer.answer)

    if result.answer.citations:
        print("\nCitations:")
        for c in result.answer.citations:
            print(f"  - {c.document} §{c.clause_id} ({c.title})")

    if result.answer.step_sequence:
        print("\nSteps:")
        for i, step in enumerate(result.answer.step_sequence, 1):
            print(f"  {i}. {step}")

    if result.answer.responsible_role:
        print(f"\nResponsible role: {result.answer.responsible_role}")

    print(f"\nConfidence: {result.answer.confidence:.2f} | Grounded: {result.answer.grounded}")


if __name__ == "__main__":
    main()
