import threading
from collections import defaultdict

_lock = threading.Lock()
_questions = {}          # task_id → prompt string
_answers   = {}          # task_id → answer string

def ask(task_id: str, prompt: str) -> str:
    """Blocking call used by the Celery task."""
    with _lock:
        _questions[task_id] = prompt
    # Wait until the browser posts an answer
    while True:
        with _lock:
            if task_id in _answers:
                ans = _answers.pop(task_id)
                del _questions[task_id]
                return ans
        threading.Event().wait(0.3)

def answer(task_id: str, value: str):
    with _lock:
        _answers[task_id] = value

def current_question(task_id: str):
    with _lock:
        return _questions.get(task_id)