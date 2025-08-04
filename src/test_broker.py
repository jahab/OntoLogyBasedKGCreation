import json
import redis
from typing import Optional

r = redis.Redis(host='localhost', port=6379, db=1, decode_responses=True)

_QUESTION_KEY = "prompt:{}"   # key template
_ANSWER_KEY   = "answer:{}"

def ask(task_id: str, prompt: str) -> str:
    q_key = _QUESTION_KEY.format(task_id)
    a_key = _ANSWER_KEY.format(task_id)

    r.setex(q_key, 3600, json.dumps({"prompt": prompt}))   # 1-hour TTL
    # blocking pop on Redis list (simple version)
    _, payload = r.blpop(a_key, timeout=0)                 # waits forever
    r.delete(q_key)
    return json.loads(payload)["value"]

def answer(task_id: str, value: str):
    a_key = _ANSWER_KEY.format(task_id)
    r.lpush(a_key, json.dumps({"value": value}))
    r.expire(a_key, 3600)

def current_question(task_id: str) -> Optional[str]:
    q_key = _QUESTION_KEY.format(task_id)
    raw = r.get(q_key)
    print(json.loads(raw))
    return json.loads(raw)["prompt"] if raw else None