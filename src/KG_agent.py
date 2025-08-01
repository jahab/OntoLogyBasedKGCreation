from langchain_community.document_loaders import PyPDFLoader
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Neo4jVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings


from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from langchain_core.runnables import RunnableConfig

from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from prompts import *
from typing import List, Dict, Literal
from utils import *
from agent_utils import *
import os
from output_parser import *

from neo4j import GraphDatabase
import uuid
import traceback
# from mem0 import MemoryClient
from refine_nodes import *
data = {
    "pdf_file":"35346_2009_39_1501_24473_Judgement_29-Oct-2020.pdf",
    "provider":"google",
    "embedding_model":"models/text-embedding-004",
    "extraction_model":"gemini-2.5-flash"
}
context = init_context(data)
load_ontology(context["neo4j_driver"])
#create_constraint
create_constraint(context["neo4j_driver"])

# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
tools = ToolNode([read_document,chunk_pdf])
# llm = llm.bind_tools([tools])
# # Nodes

# Build workflow
workflow = StateGraph(state_schema = KGBuilderState)
workflow.add_node("tools_node",tools)
# workflow.add_node("human_node", human_node)
workflow.add_node("extract_case_metadata",extract_case_metadata_ag)
workflow.add_node("read_document",read_document_ag)
workflow.add_node("chunk_pdf",chunk_pdf_ag)
workflow.add_node("read_chunk",read_chunk_ag)

workflow.add_node("extract_nodes_rels",extract_nodes_rels)
workflow.add_node("generate_embeddings",generate_embeddings)
workflow.add_node("refine_nodes",refine_nodes)

workflow.add_edge(START, "read_document")
workflow.add_edge("read_document","chunk_pdf")
workflow.add_edge("chunk_pdf","read_chunk")
workflow.add_conditional_edges("read_chunk",  lambda state: state.get("next"),{"extract_case_metadata": "extract_case_metadata", "extract_nodes_rels": "extract_nodes_rels", "generate_embeddings":"generate_embeddings" })
workflow.add_edge("extract_case_metadata","extract_nodes_rels")
workflow.add_edge("extract_nodes_rels","read_chunk")
workflow.add_edge("generate_embeddings","refine_nodes")
workflow.add_edge("refine_nodes", END)
graph = workflow.compile()


config = RunnableConfig(recursion_limit=300, **context)
graph.invoke(input = {"doc_path":"35346_2009_39_1501_24473_Judgement_29-Oct-2020.pdf"}, config = {"context":config})