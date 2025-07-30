from celery import Celery
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.documents import Document



celery = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0" 
)


# @celery.task(bind=True)
# def ask_user(self, data:dict=None):
#     total = 10
#     for step in range(1, total + 1):
#         # dummy work
#         import time; time.sleep(2)

#         # every 3rd step we ask something
#         if step % 3 == 0:
#             colour = ask(self.request.id, f"Step {step}: favourite colour?")
#             print("Got colour:", colour)

#         # progress update
#         self.update_state(
#             state="PROGRESS",
#             meta={"current": step, "total": total}
#         )

#     return {"status": "finished", "result": 42}


@celery.task(bind=True)
def invoke_graph(self, data):
    """
    Very long-running job that sometimes needs input.
    `self.request.id` is the Celery task id.
    """
    print("=====",data)
    # Index chunks
    self.update_state(
            state="PROGRESS",
            meta={"message": "Adding data to vector store"}
        )
    
  
    
    
    # total = 10
    # for step in range(1, total + 1):
    #     # dummy work
    #     import time; time.sleep(2)

    #     # every 3rd step we ask something
    #     if step % 3 == 0:
    #         colour = ask(self.request.id, f"Step {step}: favourite colour?")
    #         print("Got colour:", colour)

    #     # progress update
    #     self.update_state(
    #         state="PROGRESS",
    #         meta={"current": step, "total": total}
    #     )

    return {"status": "finished", "result": 42}

if __name__ == "__main__":
    celery.worker_main(["-A", "tasks", "worker", "--loglevel=info"])
