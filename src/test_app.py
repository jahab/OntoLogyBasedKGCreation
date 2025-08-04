from flask import Flask, request, jsonify
from test_tasks import long_job
from test_broker import current_question, answer

app = Flask(__name__)

@app.route("/start", methods=["POST"])
def start():
    task = long_job.delay(request.json or {})
    return jsonify(task_id=task.id), 202

@app.route("/status/<task_id>")
def status(task_id):
    task = long_job.AsyncResult(task_id)
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
if __name__ == '__main__':
    app.run(debug = True, host = "0.0.0.0", port = 5000)