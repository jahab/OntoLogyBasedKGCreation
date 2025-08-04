from celery import Celery
from test_broker import ask

celery = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

@celery.task(bind=True)
def long_job(self, seed):
    """
    Very long-running job that sometimes needs input.
    `self.request.id` is the Celery task id.
    """
    total = 10
    for step in range(1, total + 1):
        # dummy work
        import time; time.sleep(2)

        # every 3rd step we ask something
        if step % 3 == 0:
            colour = ask(self.request.id, f"Step {step}: favourite colour?")
            print("Got colour:", colour)

        # progress update
        self.update_state(
            state="PROGRESS",
            meta={"current": step, "total": total}
        )

    return {"status": "finished", "result": 42}

if __name__ == "__main__":
    celery.worker_main(["-A", "test_tasks", "worker", "--loglevel=info"])