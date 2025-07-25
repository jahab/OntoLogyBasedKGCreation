import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

# ---------- Page Configuration ----------
st.set_page_config(page_title="Legal Graph Builder", layout="wide")
st.markdown(
    "<style>h1 { font-size: 2.5rem; margin-bottom: 1rem; }</style>",
    unsafe_allow_html=True
)
st.title("🧠 Legal Graph Builder")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("📄 Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

    st.header("🤖 Choose LLM")
    llm_choice = st.selectbox("Select a language model", ["GPT-4", "Claude 3", "LLaMA 3", "Gemini", "Custom"])

    if st.button("🚀 Create Graph"):
        if uploaded_file:
            st.success(f"Creating graph from {uploaded_file.name} using {llm_choice}")
        else:
            st.warning("Upload a PDF to begin.")

# ---------- Graph Section ----------
st.markdown("### 🕸️ Graph View")
st.markdown("""
    <div style='border: 1px solid #DDD; border-radius: 10px; padding: 20px; box-shadow: 2px 2px 5px #eee; background-color: #fafafa;'>
""", unsafe_allow_html=True)

# Sample dummy graph
nodes = [
    Node(id="CourtCase", label="CourtCase", size=25),
    Node(id="Judge", label="Judge"),
    Node(id="Fact", label="Fact"),
]
edges = [
    Edge(source="CourtCase", target="Judge", label="hasJudge"),
    Edge(source="CourtCase", target="Fact", label="hasFact"),
]
config = Config(width=850, height=400, directed=True, nodeHighlightBehavior=True)
agraph(nodes=nodes, edges=edges, config=config)

st.markdown("</div>", unsafe_allow_html=True)

# ---------- Question Input ----------
st.markdown("### 💬 Ask a Question")

custom_css = """
<style>
.input-container {
    display: flex;
    align-items: center;
    border: 1px solid #CCC;
    border-radius: 5px;
    padding: 5px 10px;
    background-color: white;
    max-width: 850px;
}
.input-container input {
    border: none;
    outline: none;
    flex: 1;
    font-size: 16px;
    background: transparent;
}
.input-container button {
    border: none;
    background: transparent;
    cursor: pointer;
    font-size: 18px;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

col1, col2 = st.columns([1, 5])
with col2:
    question = st.text_input("", placeholder="Type your question here...", label_visibility="collapsed", key="user_question")
    send_clicked = st.button("⬆️", help="Send", use_container_width=True)

# Optionally display
if send_clicked and question.strip():
    st.info(f"🔍 Answering: {question}")
