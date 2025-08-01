from celery import Celery
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.documents import Document

from langgraph.graph import StateGraph, START, END

from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer

from agent_utils import *

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
def create_invoke_graph(self, data):
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
    
    
    context = init_context(data)
    load_ontology(context["neo4j_driver"])
    #create_constraint
    create_constraint(context["neo4j_driver"])

    # llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    tools = ToolNode([read_document,chunk_pdf])
    # llm = llm.bind_tools([tools])
    
    # Nodes
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
    # graph.invoke(input = {"doc_path":f"/data/{data['pdf_file']}"}, config = {"context":config})
  
    for chunk in graph.stream({"doc_path":f"/data/{data['pdf_file']}"}, config = {"context":config},stream_mode="custom"):
        print(chunk)
        self.update_state(
            state="PROGRESS",
            meta={"update":chunk}
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
