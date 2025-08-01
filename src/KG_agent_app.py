from flask import Flask, jsonify, request, make_response

from langgraph.graph import StateGraph, START, END

from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig

import redis

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
from tasks import *
from broker import *

# creating a Flask app
app = Flask(__name__)


@app.route('/ping', methods = ['GET'])
def ping():
    return jsonify({'ping': 'KG_agent_pong'})


@app.route('/create_graph', methods = ['POST'])
def create_graph():
    data = request.json
    
    # context = init_context(data)
    # load_ontology(context["neo4j_driver"])
    # #create_constraint
    # create_constraint(context["neo4j_driver"])

    # # llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # tools = ToolNode([read_document,chunk_pdf])
    # # llm = llm.bind_tools([tools])
    # # # Nodes

    # # Build workflow
    # workflow = StateGraph(state_schema = KGBuilderState)
    # workflow.add_node("tools_node",tools)
    # # workflow.add_node("human_node", human_node)
    # workflow.add_node("extract_case_metadata",extract_case_metadata_ag)
    # workflow.add_node("read_document",read_document_ag)
    # workflow.add_node("chunk_pdf",chunk_pdf_ag)
    # workflow.add_node("read_chunk",read_chunk_ag)

    # workflow.add_node("extract_nodes_rels",extract_nodes_rels)
    # workflow.add_node("generate_embeddings",generate_embeddings)
    # workflow.add_node("refine_nodes",refine_nodes)

    # workflow.add_edge(START, "read_document")
    # workflow.add_edge("read_document","chunk_pdf")
    # workflow.add_edge("chunk_pdf","read_chunk")
    # workflow.add_conditional_edges("read_chunk",  lambda state: state.get("next"),{"extract_case_metadata": "extract_case_metadata", "extract_nodes_rels": "extract_nodes_rels", "generate_embeddings":"generate_embeddings" })
    # workflow.add_edge("extract_case_metadata","extract_nodes_rels")
    # workflow.add_edge("extract_nodes_rels","read_chunk")
    # workflow.add_edge("generate_embeddings","refine_nodes")
    # workflow.add_edge("refine_nodes", END)
    # graph = workflow.compile()
    # config = RunnableConfig(recursion_limit=300, **context)
    # task = invoke_graph.delay(graph)
    # graph.invoke(input = {"doc_path":f"/data/{data['pdf_file']}"}, config = {"context":config})
    task = create_invoke_graph.delay(data)
    
    # r = redis.Redis(host="redis", port=6379, db=1)
    # r.setex(f"task_owner:{task.id}", 7200, user_id)

    return jsonify(task_id=task.id), 202


@app.route("/status/<task_id>")
def status(task_id):
    task = create_invoke_graph.AsyncResult(task_id)
    if task.state == "PENDING":
        resp = {"state": "PENDING"}
    elif task.state == "PROGRESS":
        resp = {"state": "PROGRESS", "meta": task.info}
    elif task.state == "SUCCESS":
        resp = {"state": "SUCCESS", "result": task.result}
    else:  # FAILURE
        resp = {"state": task.state, "error": str(task.info)}
    return jsonify(resp)

@app.route("/prompt/<task_id>")
def prompt(task_id):
    q = current_question(task_id)
    return jsonify(question=q) if q else ("", 204)

@app.route("/answer/<task_id>", methods=["POST"])
def answer_route(task_id):
    answer(task_id, request.json["value"])
    return "", 204


# driver function
if __name__ == '__main__':
    app.run(debug = True, host = "0.0.0.0", port = 4044)