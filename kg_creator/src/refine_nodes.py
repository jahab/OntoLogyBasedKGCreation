from utils import *
from prompts import *
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from qdrant_client import models
from broker import ask
class RefineNodes:
    def __init__(self, driver, vector_db_client, vector_store, coll_name, model):
        self.driver = driver
        self.vector_store = vector_store
        self.threshold = 0.6
        self.model = model
        self.vector_db_client = vector_db_client
        self.collection_name = coll_name
        self.create_prompt_template()

    def create_prompt_template(self):
        self.refine_nodes_template = PromptTemplate(
            template=REFINE_NODES_PROMPT
        )


    def remove_emenent_id(self, node_list:list, id_to_remove:str):
        
        return [node for node in node_list if node.element_id != id_to_remove]

    
    def refine_nodes(self, task_id:str|None):
        # use the calculated embeddings
        # using the embeddings identify the nodes that can be merged
        # should yu use GPT to ask if the nodes can be merged? Or ask user?
        
        refine_nodes_chain = self.refine_nodes_template | self.model
        with self.driver.session() as session:
            result = session.execute_read(get_nodes_and_rels)
        unique_nodes = set()
        for record in result:
            unique_nodes.add(record["n"])
        
        unique_nodes = list(unique_nodes)
        # for un in unique_nodes:
        for i in range(len(unique_nodes)-1,-1,-1): # loop backwards as you are removing the elements dynamically from the list
            # search in vector DB but search what?
            # for every unique node search in vectorDB if similarity exists with other nodes
            # if similarity greater than a threshold then call merge nodes
            nodes = self.vector_store.similarity_search_with_score(query = f"{unique_nodes[i].labels} {unique_nodes[i].items()}", 
                                                                   k=5,
                                                                   filter=models.Filter(
                                                                    must_not=[
                                                                        models.FieldCondition(
                                                                            key="metadata.element_id",
                                                                            match=models.MatchValue(
                                                                                value =  unique_nodes[i].element_id
                                                                            ),
                                                                        ),
                                                                    ]
                                                                    ) 
                                                                )
            for n in nodes:
                score = n[1]
                if score > self.threshold:
                    # find best node to merge
                    #invoke the model with text what is the text????
                    resp = refine_nodes_chain.invoke({"node1": f"{unique_nodes[i].labels} {unique_nodes[i].items()}",
                                                      "node2": f"{n[0].metadata} {n[0].page_content} " 
                                                      })
                    print("[refine Nodes]: ",resp)
                    if "yes" in resp.content.lower():
                        print(task_id)
                        if task_id is None:
                            print("comes in if=======")
                            user_input = input(f"[MERGE NODES]\n\nNode1: {unique_nodes[0]} \n\nNode2: {n[0]}\n\nPlease Select option\nMerge Node1 into Node2: press 1\nMerge Node2 into Node1: press 2\nDiscard: Press 3\nYour answer:")
                        else:
                            print("comes in else=======")
                            user_input = ask(task_id, f"[MERGE NODES]\n\nNode1: {unique_nodes[0]} \n\nNode2: {n[0].page_content}\n\nPlease Select option\nMerge Node1 into Node2: press 1\nMerge Node2 into Node1: press 2\nDiscard: Press 3\nYour answer:")
                        if "1" in user_input.lower():
                            ret_val = merge_by_id(self.driver, unique_nodes[i].element_id, n[0].metadata["element_id"])
                            if ret_val:
                                self.vector_store.delete(ids = [n[0].metadata["_id"]])
                                del unique_nodes[i]
                        elif "2" in user_input.lower(): # TODO: FIXME: delete the node from the vector DB properly->Done but neess testing
                            ret_val = merge_by_id(self.driver, n[0].metadata["element_id"], unique_nodes[i].element_id)
                            if ret_val:
                                self.vector_store.delete(ids = [n[0].metadata["_id"]])
                                self.vector_db_client.delete(points=models.Filter(
                                    must=[
                                        models.FieldCondition(
                                                key="metadata.element_id", 
                                                match=models.MatchValue(value=unique_nodes[i].element_id)
                                                )
                                            ]
                                        )
                                    )
                                del unique_nodes[i]
                        elif "3" in user_input.lower():
                            pass
                    
            
            
            