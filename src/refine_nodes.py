from utils import *
from prompts import *
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

class RefineNodes:
    def __init__(self, driver, vector_store, model):
        self.driver = driver
        self.vector_store = vector_store
        self.threshold = 0.6
        self.model = model
        self.create_prompt_template()

    def create_prompt_template(self):
        self.refine_nodes_template = PromptTemplate(
            template=REFINE_NODES_PROMPT
        )


    def remove_emenent_id(self, node_list:list, id_to_remove:str):
        
        return [node for node in node_list if node.element_id != id_to_remove]

    
    def refine_nodes(self):
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
        for i in range(len(unique_nodes)-1,-1,-1):
            #search in vector DB but search what?
            # for every node search if similarity exists with other nodes
            # if similarity greater than thresh then call merge nodes
            nodes = self.vector_store.similarity_search_with_score(f"{unique_nodes[i].labels} {unique_nodes[i].items()}", k=5)
            for n in nodes:
                score = n[1]
                if score > self.threshold:
                    # find best node to merge
                    #invoke the model with text what is the text????
                    resp = refine_nodes_chain.invoke({"node1": f"{unique_nodes[i].labels} {unique_nodes[i].items()}",
                                                      "node2": f"{n[0].metadata} {n[0].page_content} " 
                                                      })
                    if "yes" in resp.content.lower():
                        print("[MERGE NODES]",unique_nodes[i], n[0].page_content)
                        user_input = input("get User input answer in y or n")
                        if user_input.lower() == "y":
                            merge_by_id(self.driver, unique_nodes[i].element_id, n[0].metadata["element_id"])
                            element_id_to_remove = n[0].metadata["element_id"]
                            self.vector_store.delete(ids = [n[0].metadata["_id"]])
                            unique_nodes.remove()
                    
                    
            
            
            