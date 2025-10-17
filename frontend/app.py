# ---------- 1) Imports ----------
import os
import streamlit as st
import requests
# import extra_streamlit_components as stx
from streamlit_agraph import agraph, Node, Edge, Config

import pymongo

# myclient = pymongo.MongoClient("mongodb://localhost:27017")
myclient = pymongo.MongoClient("mongodb://mongodb:27017")
mongo_db = myclient["db"]

# UPLOAD_DIR = "/data/"
UPLOAD_DIR = "data/"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- 2) Page Config (Only once, at top) ----------
st.set_page_config(page_title="Legal Graph Builder", layout="wide")

# ---------- 3) Backend base URL ----------
BACKEND = "http://login-service:5000"
# BACKEND = "http://localhost:5000"

# ---------- 4) Helpers ----------
def login(username, password):
    return requests.post(f"{BACKEND}/signin", json={"username": username, "password": password})

def signup(username, password):
    return requests.post(f"{BACKEND}/signup", json={"username": username, "password": password})

def reset_password(username, new_password):
    return requests.post(f"{BACKEND}/forgetpwd", json={"username": username, "new_password": new_password})


@st.cache_data(ttl=60)                    # refresh every 60 s
def fetch_completed_files():
    coll     = mongo_db["docs"]
    docs     = list(coll.find({"status": "completed"}, {"name": 1, "_id": 0}))
    return [d["name"] for d in docs]


# ---------- DUMMY GRAPH FETCHER ----------
def dummy_fetch_graph(filename: str):
    """Pretend we hit a graph DB and got back nodes & rels."""
    nodes = [
        {"id": f"{filename}#0", "label": "Node-A", "type": "Person"},
        {"id": f"{filename}#1", "label": "Node-B", "type": "Org"},
    ]
    edges = [
        {"source": f"{filename}#0", "target": f"{filename}#1", "rel": "WORKS_FOR"},
    ]
    return nodes, edges

# ---------- 5) Auth state and JWT token ----------
# cookie_manager = stx.CookieManager()
# token = cookie_manager.get("jwt") or st.session_state.get("jwt_token")
token = st.session_state.get("jwt_token")

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
            print("=================", token)
            # cookie_manager.set("jwt", token)
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
    left, graph_col = st.columns([1, 50], gap="small")          # 1-col sidebar, 2-col right panel
    
    # graph_col = right.columns(1)    # split right area
    # graph_col, chat_col = right.columns(1)    # split right area
    
    # Sidebar
    with left:
        with st.sidebar:
            st.header("👤 Logged in")
            if st.button("Logout"):
                # print(cookie_manager)
                # cookie_manager.delete("jwt")
                st.session_state.pop("jwt_token", None)
                st.rerun()


            st.header("📄 Documents with completed knowledge-graph")

            completed = fetch_completed_files()
            if not completed:
                st.info("No graphs ready yet.")
            else:
                # st.write("Click a file to load graph of the document:")
                cols = st.columns(4)               # 4 buttons per row
                file_container = st.container(border=True)
            for idx, fname in enumerate(completed):
                col = cols[idx % 4]
                # if col.button(fname, key=f"btn_{idx}"):
                if file_container.button(fname, key=f"btn_{idx}"):
                    with st.spinner(f"Loading graph for {fname}…"):
                        raw_nodes, raw_edges = dummy_fetch_graph(fname)
                    # # convert
                    nodes = [Node(id=n["id"], label=n["label"], title=n["type"]) for n in raw_nodes]
                    edges = [Edge(source=e["source"], target=e["target"], label=e["rel"]) for e in raw_edges]
                    # persist to session_state so the main area picks it up
                    st.session_state.last_graph_nodes = nodes
                    st.session_state.last_graph_edges = edges
                    st.rerun()   # optional: immediate refresh

            st.header("📄 Upload Document")
            uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])
            if uploaded_file is not None:
                save_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                with open(save_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"File saved at: {save_path}")


            # st.header("🤖 Choose LLM")
            # llm_choice = st.selectbox("Select a language model", ["GPT-4", "Claude 3", "LLaMA 3", "Gemini", "Custom"])

            # ---------- 1. CHAT MODEL PICKER ----------
            st.header("🤖 Choose LLM")

            chat_providers = {
                "OpenAI": ["gpt-4o", "gpt-4o-mini", "o1", "gpt-4.1", "gpt-nano"],
                "Google": ["gemini-2.5-flash", "gemini-2.5-pro", "gemma-2b", "gemma-3b"],
                "Anthropic": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "Meta": ["llama3-70b", "llama3-8b"],
                "Custom": ["custom-endpoint"],
            }

            chat_provider = st.selectbox("Provider", list(chat_providers.keys()), key="model_provider")
            chat_model   = st.selectbox("Model", chat_providers[chat_provider], key="extraction_model")

            # ---------- 2. EMBEDDING MODEL PICKER ----------
            st.header("🔡 Choose Embedding Model")

            emb_providers = {
                "OpenAI": ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
                "Google": ["models/text-embedding-004", "multilingual-embedding"],
                "Sentence-Transformers": ["all-MiniLM-L6-v2", "all-mpnet-base-v2"],
                "Custom": ["custom-embed-endpoint"],
            }

            emb_provider = st.selectbox("Provider", list(emb_providers.keys()), key="embedding_provider")
            emb_model    = st.selectbox("Model", emb_providers[emb_provider], key="embedding_model")


            if st.button("🚀 Create Graph"):
                if uploaded_file:
                    st.success(f"Creating graph from **{uploaded_file.name}** using {chat_provider} **{chat_model}**")
                    json_query = {
                            "pdf_file":uploaded_file.name,
                            "model_provider":chat_provider.lower(),
                            "embedding_provider":emb_provider.lower(),
                            "embedding_model":emb_model.lower(),
                            "extraction_model":chat_model.lower()
                        }
                    requests.post("http://kg_app:4044/create_graph",json={"pdf_file":uploaded_file.name})
                else:
                    st.warning("Upload a PDF to begin.")


    # with graph_col:

    #     st.markdown("### 🕸️ Graph View")
    #     st.write("Column width test")
    #     nodes = [Node(id="CourtCase", label="CourtCase", size=25),
    #             Node(id="Judge", label="Judge"),
    #             Node(id="Fact", label="Fact")]
    #     edges = [Edge(source="CourtCase", target="Judge", label="hasJudge"),
    #                 Edge(source="CourtCase", target="Fact", label="hasFact")]
    #     print(nodes)
        
    #     # st.write("Debug below 👇")
    #     graph_container = st.container(border=True,height=500)
    #     with graph_container:
    #         config = Config(width=600, 
    #                     height=500, 
    #                     directed=True, 
    #                     nodeHighlightBehavior=True, 
    #         )
    #         agraph(nodes=nodes, edges=edges, config=config)
        # st.markdown("</div>", unsafe_allow_html=True)



    nodes = []
    edges = []
    # left, right = st.columns([1, 2])          # 1-col sidebar, 2-col right panel
    # graph_col, chat_col = right.columns(2)    # split right area
    nodes.append( Node(id="Spiderman", 
                    label="Peter Parker", 
                    size=25, 
                    shape="circularImage",
                    image="http://marvel-force-chart.surge.sh/marvel_force_chart_img/top_spiderman.png") 
                ) # includes **kwargs
    nodes.append( Node(id="Captain_Marvel", 
                    size=25,
                    shape="circularImage",
                    image="http://marvel-force-chart.surge.sh/marvel_force_chart_img/top_captainmarvel.png") 
                )
    edges.append( Edge(source="Captain_Marvel", 
                    label="friend_of", 
                    target="Spiderman", 
                    # **kwargs
                    ) 
                ) 



    with graph_col:
        graph_container = st.container(border=True,height=700)
        with graph_container:
            config = Config(width="100%", 
                            height=950, 
                            directed=True, 
                            nodeHighlightBehavior=True, 
                            collapsible=True,
                            physics={"barnesHut": {
                                    "gravitationalConstant": -100,
                                    "centralGravity": 0.3,
                                    "springLength": 95
                                    }
                                    }
                )
            return_value = agraph(nodes=nodes, 
                                edges=edges, 
                                config=config)




    # Ask Question
    # with chat_col:
    # st.markdown("### 💬 Ask a Question")

    # with st.container():
    #     st.markdown("""
    #         <style>
    #         .ask-box {
    #             display: flex;
    #             border: 1px solid #CCC;
    #             border-radius: 20px;
    #             padding: 5px 15px;
    #             background: white;
    #             box-shadow: 1px 1px 4px rgba(0,0,0,0.05);
    #             align-items: center;
    #             max-width: 600px;
    #         }
    #         .ask-box input {
    #             border: none;
    #             outline: none;
    #             flex-grow: 1;
    #             font-size: 16px;
    #             padding: 8px;
    #             width: 100%;
    #         }
    #         .ask-box button {
    #             border: none;
    #             background: transparent;
    #             font-size: 20px;
    #             cursor: pointer;
    #         }
    #         </style>
    #     """, unsafe_allow_html=True)

    #     col1, col2 = st.columns([1, 5])
    #     with col2:
    #         question = st.text_input("Ask Something", placeholder="Ask something about the graph...", key="question_input", label_visibility="collapsed")
    #         send = st.button("⬆️", help="Send", use_container_width=True)

    # if send and question.strip():
    #     st.info(f"🔍 Processing question: `{question}`")

# if st.button("Logout"):
#     cookie_manager.delete("jwt")
#     st.session_state.clear()
#     st.rerun()

