from flask import Flask, jsonify, request, make_response

from langgraph.graph import StateGraph, START, END

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


# creating a Flask app
app = Flask(__name__)


@app.route('/', methods = ['GET'])
def ping():
    return jsonify({'ping': 'pong'})


@app.route('/create_graph/<guid>', methods = ['GET'])
def create_graph():
    data = request.params
    context = init_context()
    load_ontology(context["neo4j_driver"], guid)
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
    return jsonify({'status': 0})