"""
Streamlit demo UI for DeskOracle -- submit a ticket description and see the
AI triage suggestion live. Calls the triage engine directly (no need to
run the FastAPI server separately for this demo).

Run: streamlit run app_ui.py
"""
import streamlit as st

from backend.triage import triage

st.set_page_config(page_title="DeskOracle", page_icon="🎫", layout="centered")

st.title("🎫 DeskOracle")
st.caption("AI-assisted IT helpdesk ticket triage (RAG + LLM agent, with offline fallback)")

with st.form("ticket_form"):
    description = st.text_area(
        "Describe the issue",
        placeholder="e.g. My VPN keeps disconnecting every few minutes and I can't reconnect",
        height=120,
    )
    submitted = st.form_submit_button("Triage Ticket")

if submitted:
    if len(description.strip()) < 5:
        st.error("Please enter a longer description.")
    else:
        with st.spinner("Analyzing ticket..."):
            result = triage(description)

        mode_label = "🤖 LLM agent" if result.mode == "llm" else "⚙️ Rule-based fallback (no API key set)"
        st.info(f"Mode: {mode_label}")

        col1, col2 = st.columns(2)
        col1.metric("Predicted Category", result.predicted_category.replace("_", " / "))
        priority_color = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
        col2.metric("Predicted Priority", f"{priority_color.get(result.predicted_priority, '')} {result.predicted_priority}")

        st.subheader("Suggested Response")
        st.write(result.suggested_response)

        if result.kb_matches:
            st.subheader("Relevant Knowledge Base Articles")
            for match in result.kb_matches:
                st.write(f"- **{match.title}** ({match.category}) -- relevance {match.score:.2f}")

st.divider()
st.caption(
    "Demonstrates a RAG-backed triage agent (Software), a synthetic ticket "
    "dataset with classifier evaluation (Data Analytics), and this UI "
    "(Product Design)."
)
