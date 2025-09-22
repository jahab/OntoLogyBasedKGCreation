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
from broker import current_question, answer
from global_import import *

# creating a Flask app
app = Flask(__name__)


@app.route('/ping', methods = ['GET'])
def ping():
    return jsonify({'ping': 'KG_agent_pong'})


@app.route('/create_graph', methods = ['POST'])
def create_graph():
    data = request.json
    data["username"] = "admin" #TODO:FIXME: Take user name from session_id
    user_collection = mongo_db["users"]
    task = create_invoke_graph.delay(data)
    user_collection.update_one({"username": "admin"}, {"$set": {"task_id":task.id}})
    # r = redis.Redis(host="redis", port=6379, db=1)
    # r.setex(f"task_owner:{task.id}", 7200, user_id)

    return jsonify(task_id=task.id), 202


@app.route("/status",  methods = ['POST'])
def status():
    data = request.json
    task_id = data["task_id"]
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

@app.route("/prompt",methods = ['POST'])
def prompt():
    data = request.json
    task_id = data["task_id"]
    q = current_question(task_id)
    print(q)
    return jsonify(question=q) if q else jsonify({"message":"no questions in q"})

@app.route("/answer", methods=["POST"])
def answer_route():
    data = request.json
    task_id = data["task_id"]
    answer(task_id, request.json["value"])
    return "", 204


# driver function
if __name__ == '__main__':
    app.run(debug = True, host = "0.0.0.0", port = 4044)