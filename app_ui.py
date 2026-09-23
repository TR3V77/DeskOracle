"""
Streamlit demo UI for DeskOracle -- submit a ticket description and see the
AI triage suggestion live. Calls the triage engine directly (no need to
run the FastAPI server separately for this demo).

Run: streamlit run app_ui.py
"""
import streamlit as st

from backend.triage import triage

st.set_page_config(page_title="DeskOracle", page_icon="🎫", layout="centered")

st.markdown(
    """
    <style>
        .block-container { padding-top: 2.5rem; max-width: 800px; }
        .priority-pill {
            display: inline-block; padding: 0.35rem 0.9rem; border-radius: 8px;
            font-weight: 700; font-size: 1.05rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("## 🎫 DeskOracle")
st.caption("AI-assisted IT helpdesk ticket triage — RAG retrieval + LLM agent, with a deterministic offline fallback")

st.divider()

if "description" not in st.session_state:
    st.session_state.description = ""

st.markdown("**Try an example, or describe your own issue below:**")
examples = {
    "🔌 VPN dropping": "My VPN keeps disconnecting every few minutes and I can't reconnect",
    "🔒 Locked out": "I forgot my password and I'm locked out of my account",
    "🎣 Phishing email": "I think I clicked a phishing link in a suspicious email",
    "🖨️ Printer offline": "The printer on the 3rd floor is offline and won't print",
}
example_cols = st.columns(4)
for col, (label, text) in zip(example_cols, examples.items()):
    if col.button(label, use_container_width=True):
        st.session_state.description = text

with st.container(border=True):
    description = st.text_area(
        "Describe the issue",
        key="description",
        placeholder="e.g. My VPN keeps disconnecting every few minutes and I can't reconnect",
        height=120,
    )
    submitted = st.button("Triage Ticket", type="primary")

if submitted:
    if len(description.strip()) < 5:
        st.error("Please enter a longer description.")
    else:
        with st.spinner("Analyzing ticket..."):
            result = triage(description)

        mode_label = "🤖 LLM agent" if result.mode == "llm" else "⚙️ Rule-based fallback (no API key set)"
        st.info(f"Mode: {mode_label}")

        priority_colors = {
            "Critical": ("#f87171", "rgba(248, 113, 113, 0.15)"),
            "High": ("#fb923c", "rgba(251, 146, 60, 0.15)"),
            "Medium": ("#facc15", "rgba(250, 204, 21, 0.15)"),
            "Low": ("#4ade80", "rgba(74, 222, 128, 0.15)"),
        }
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Predicted Category", result.predicted_category.replace("_", " / "))
        with col2:
            fg, bg = priority_colors.get(result.predicted_priority, ("#94a3b8", "rgba(148, 163, 184, 0.15)"))
            st.caption("Predicted Priority")
            st.markdown(
                f'<span class="priority-pill" style="color:{fg}; background:{bg};">'
                f'{result.predicted_priority}</span>',
                unsafe_allow_html=True,
            )

        st.subheader("Suggested Response")
        st.write(result.suggested_response)

        if result.kb_matches:
            st.subheader("Relevant Knowledge Base Articles")
            for match in result.kb_matches:
                mcol1, mcol2 = st.columns([3, 1])
                mcol1.markdown(f"**{match.title}**  \n*{match.category.replace('_', ' / ')}*")
                mcol2.progress(min(match.score, 1.0), text=f"{match.score:.2f}")

st.divider()
st.caption(
    "Demonstrates a RAG-backed triage agent (Software), a synthetic ticket "
    "dataset with classifier evaluation (Data Analytics), and this UI "
    "(Product Design). [View source on GitHub](https://github.com/TR3V77/DeskOracle)"
)
