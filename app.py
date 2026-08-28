"""
interface/app.py
-------------------
Optional lightweight Streamlit UI (Good-to-Have: "A lightweight UI
(Streamlit / Gradio) with citation highlighting"). Not required for the
Mandatory deliverables; the CLI (interface/cli.py) is the primary interface.

Run:
    streamlit run interface/app.py
"""

from __future__ import annotations

import streamlit as st

from src.pipeline import RAGPipeline

st.set_page_config(page_title="Hospital Policy & SOP Assistant", layout="centered")
st.title("Hospital Policy & SOP Assistant")
st.caption(
    "Synthetic demo corpus only — grounded, cited answers with abstention when the "
    "corpus does not support a confident response."
)


@st.cache_resource
def get_pipeline() -> RAGPipeline:
    return RAGPipeline()


question = st.text_input("Ask a policy or SOP question:")

if st.button("Ask") and question.strip():
    with st.spinner("Retrieving and generating..."):
        pipeline = get_pipeline()
        result = pipeline.ask(question)

    if result.answer.abstained:
        st.warning("Abstained — insufficient grounded evidence in the corpus.")
    st.markdown(f"### Answer\n{result.answer.answer}")

    if result.answer.citations:
        st.markdown("### Citations")
        for c in result.answer.citations:
            st.markdown(f"- **{c.document}** §{c.clause_id} — _{c.title}_")

    if result.answer.step_sequence:
        st.markdown("### Steps")
        for i, step in enumerate(result.answer.step_sequence, 1):
            st.markdown(f"{i}. {step}")

    if result.answer.responsible_role:
        st.markdown(f"**Responsible role:** {result.answer.responsible_role}")

    st.markdown(
        f"**Confidence:** {result.answer.confidence:.2f} &nbsp;|&nbsp; "
        f"**Grounded:** {result.answer.grounded}"
    )

    with st.expander("Retrieved chunks (debug)"):
        for c in result.retrieved_chunks:
            st.text(f"[{c.score:.3f}] {c.metadata.get('doc_id')} §{c.metadata.get('clause_id')}")
            st.caption(c.text)
