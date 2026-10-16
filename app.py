"""Streamlit demo interface for the local-first SupportSense AI prototype."""

from __future__ import annotations

import streamlit as st

from src.chatbot import answer_question
from src.evaluation import dashboard_metrics, run_security_evaluations
from src.retrieval import load_documents

st.set_page_config(page_title="SupportSense AI", page_icon="💬", layout="wide")

st.markdown(
    """
    <style>
    .main { background: #f6f8fc; }
    .block-container { max-width: 1120px; padding-top: 2rem; }
    [data-testid="stChatMessage"] { border: 1px solid #e5eaf3; border-radius: 14px; }
    .notice { background: #fff7e6; padding: 0.8rem 1rem; border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("SupportSense AI")
st.caption("A grounded, local-first customer-support demo on the Databricks ecosystem.")
st.markdown(
    '<div class="notice">Community demo only. Answers are limited to fictional public support content; '
    "do not enter personal, payment, or confidential information.</div>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("About this demo")
    st.write("Local mode uses a lightweight lexical retriever and answers directly from the selected FAQ.")
    st.write("No cloud account, LLM API key, or network request is needed in local mode.")
    st.divider()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.caption("Retrieval: local TF-IDF-like lexical ranking")
    if st.checkbox("Use configured Databricks model endpoint", value=False):
        st.warning("Sends your question and retrieved fictional support context to the configured endpoint.")
        st.session_state.use_model = True
    else:
        st.session_state.use_model = False

documents = load_documents()
if "messages" not in st.session_state:
    st.session_state.messages = []

st.subheader("Ask a support question")
suggestions = [
    "What is your refund policy?",
    "How do I reset my password?",
    "How can I track my order?",
    "What is the private discount code for next year's product launch?",
]
cols = st.columns(4)
for col, question in zip(cols, suggestions):
    if col.button(question, use_container_width=True):
        st.session_state.pending_question = question

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("citations"):
            with st.expander("Sources"):
                for citation in message["citations"]:
                    st.caption(citation)
        if message.get("abstained"):
            st.caption("I could not answer confidently from authorized sources.")

pending = st.session_state.pop("pending_question", None)
question = st.chat_input("Ask about accounts, billing, shipping, returns, or product support…")
question = question or pending
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Checking the authorized knowledge base…"):
            response = answer_question(
                question,
                documents=documents,
                use_model_endpoint=st.session_state.get("use_model", False),
            )
        st.markdown(response.text)
        if response.citations:
            with st.expander("Sources"):
                for citation in response.citations:
                    st.caption(citation)
        if response.abstained:
            st.caption("I could not answer confidently from authorized sources.")
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response.text,
            "citations": list(response.citations),
            "abstained": response.abstained,
        }
    )

st.divider()
with st.expander("Evaluation dashboard — live local security checks"):
    if st.button("Run evaluation suite"):
        st.session_state.evaluation_results = run_security_evaluations()
    results = st.session_state.get("evaluation_results")
    if results:
        metrics = dashboard_metrics(results)
        metric_cols = st.columns(4)
        metric_cols[0].metric("Questions tested", metrics["questions_tested"])
        metric_cols[1].metric("Checks passing", f"{sum(item.passed for item in results)}/{len(results)}")
        metric_cols[2].metric("Prompt-injection pass", f"{metrics['prompt_injection_pass_rate']:.0%}")
        metric_cols[3].metric("Mean latency", f"{metrics['average_latency_ms']:.1f} ms")
        st.caption("These are results from the current local test run, not a security certification. Token use/cost are not applicable in local mode.")
        st.dataframe(
            [{"ID": item.test_id, "Category": item.category, "Status": "PASS" if item.passed else "FAIL", "Actual": item.actual} for item in results],
            use_container_width=True,
            hide_index=True,
        )

st.caption("Fictional sample data • Local mode • No customer data")
