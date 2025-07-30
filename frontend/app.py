# ---------- 1) Imports ----------
import os
import streamlit as st
import requests
import extra_streamlit_components as stx
from streamlit_agraph import agraph, Node, Edge, Config

UPLOAD_DIR = "/data/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- 2) Page Config (Only once, at top) ----------
st.set_page_config(page_title="Legal Graph Builder", layout="wide")

# ---------- 3) Backend base URL ----------
BACKEND = "http://login-service:5000"

# ---------- 4) Helpers ----------
def login(username, password):
    return requests.post(f"{BACKEND}/signin", json={"username": username, "password": password})

def signup(username, password):
    return requests.post(f"{BACKEND}/signup", json={"username": username, "password": password})

def reset_password(username, new_password):
    return requests.post(f"{BACKEND}/forgetpwd", json={"username": username, "new_password": new_password})

# ---------- 5) Auth state and JWT token ----------
cookie_manager = stx.CookieManager()
token = cookie_manager.get("jwt") or st.session_state.get("jwt_token")

# ---------- 6) Login / Sign-up ----------
if token is None:
    st.title("🔐 Welcome to Legal Graph Builder")

    # a single flag to open/close the modal
    if "show_signup_modal" not in st.session_state:
        st.session_state.show_signup_modal = False

    # ---- Login form ----
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        col1, col2 = st.columns([2, 1])
        with col1:
            login_submitted = st.form_submit_button("Log In", use_container_width=True)
        with col2:
            if st.form_submit_button("Sign Up", use_container_width=True):
                st.session_state.show_signup_modal = True
                st.rerun()  # <- force re-render so modal appears immediately

    # ---- Handle login ----
    if login_submitted:
        res = login(username, password)
        if res.status_code == 200:
            token = res.json().get("token")
            cookie_manager.set("jwt", token)
            st.session_state.jwt_token = token
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error(res.json().get("error", "Login failed"))

    # ---- Sign-up dialog (shown as an expander instead of CSS modal) ----
    if st.session_state.show_signup_modal:
        with st.expander("Create an account", expanded=True):
            with st.form("signup_modal_form"):
                new_user = st.text_input("Username", key="su_user")
                new_pass = st.text_input("Password", type="password", key="su_pass")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("Register"):
                        res = signup(new_user, new_pass)
                        if res.status_code == 201:
                            st.success("🎉 Account created! Please log in.")
                            st.session_state.show_signup_modal = False
                            st.rerun()
                        else:
                            st.error(res.json().get("error", "Signup failed"))
                with col2:
                    if st.form_submit_button("Cancel"):
                        st.session_state.show_signup_modal = False
                        st.rerun()
# ---------- 7) Main App ----------
else:
    st.title("🧠 Legal Graph Builder")

    # Sidebar
    with st.sidebar:
        st.header("👤 Logged in")
        if st.button("Logout"):
            cookie_manager.delete("jwt")
            st.rerun()

        st.header("📄 Upload Document")
        uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])
        if uploaded_file is not None:
            save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File saved at: {save_path}")

        st.header("🤖 Choose LLM")
        llm_choice = st.selectbox("Select a language model", ["GPT-4", "Claude 3", "LLaMA 3", "Gemini", "Custom"])

        if st.button("🚀 Create Graph"):
            if uploaded_file:
                st.success(f"Creating graph from **{uploaded_file.name}** using **{llm_choice}**")
                requests.post("http://kg_app:4044/create_graph",json={"pdf_file":uploaded_file.name})
            else:
                st.warning("Upload a PDF to begin.")

    # Graph UI
    st.markdown("### 🕸️ Graph View")
    st.markdown(
        """
        <div style='border: 2px solid #DDD; border-radius: 10px; padding: 20px; 
                    box-shadow: 2px 2px 5px #eee; background-color: #fcfcfc;'>
        """,
        unsafe_allow_html=True,
    )

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

    # Ask Question
    st.markdown("### 💬 Ask a Question")

    with st.container():
        st.markdown("""
            <style>
            .ask-box {
                display: flex;
                border: 1px solid #CCC;
                border-radius: 20px;
                padding: 5px 15px;
                background: white;
                box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
                align-items: center;
                max-width: 600px;
            }
            .ask-box input {
                border: none;
                outline: none;
                flex-grow: 1;
                font-size: 16px;
                padding: 8px;
                width: 100%;
            }
            .ask-box button {
                border: none;
                background: transparent;
                font-size: 20px;
                cursor: pointer;
            }
            </style>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns([1, 5])
        with col2:
            question = st.text_input("", placeholder="Ask something about the graph...", key="question_input")
            send = st.button("⬆️", help="Send", use_container_width=True)

    if send and question.strip():
        st.info(f"🔍 Processing question: `{question}`")
    
    if st.button("Logout"):
        cookie_manager.delete("jwt")
        st.session_state.clear()
        st.rerun()
