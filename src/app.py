from langchain_community.document_loaders import PyPDFLoader
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import Neo4jVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from prompts import *
from typing import List, Dict
from utils import *
from dotenv import load_dotenv
import os
from output_parser import *
from neo4j import GraphDatabase
import uuid
import traceback
from mem0 import MemoryClient



def retrieve_context(query: str, user_id: str) -> List[Dict]:
    """Retrieve relevant context from Mem0"""
    memories = mem0.search(query, user_id=user_id)
    seralized_memories = ' '.join([mem["memory"] for mem in memories])
    context = [
        { 
            "content": f"Relevant information: {seralized_memories}"
        },
        {
            "role": "user",
            "content": query
        }
    ]
    return context

def save_interaction(user_id: str, user_input: str, assistant_response: str):
    """Save the interaction to Mem0"""
    interaction = [
        {
          "role": "user",
          "content": user_input
        },
        {
            "role": "assistant",
            "content": assistant_response
        }
    ]
    mem0.add(interaction, user_id=user_id)


if __name__ == "__main__":
    load_dotenv()
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "admin@123"
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["MEM0_API_KEY"] = os.getenv("MEM0_API_KEY")
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    driver = GraphDatabase.driver(uri, auth=(username, password))
    #import ontology
    load_ontology(driver)

    #create_constraint
    create_constraint(driver)
    
    #read the Document
    file_path = ("/mnt/c/Users/jafarhabshee/Downloads/Judgementsq/Judgements/Cases/35346_2009_39_1501_24473_Judgement_29-Oct-2020.pdf")
    loader = PyPDFLoader(file_path)
    pages = []
    text = ""

    for page in loader.lazy_load():
        pages.append(page)
        text = text+"\n"+page.page_content
    
    doc =  Document(page_content=text, metadata={"source": "local"})

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=20)

    text_chunks = text_splitter.split_text(text)    

    case_metadata_parser = JsonOutputParser(pydantic_object=CaseMetadataParser)
    metadata_extract_template = ChatPromptTemplate(
        messages = [("system", METADATA_EXTRACTION_PROMPT),("user","{text}") ],
        partial_variables={"format_instructions": case_metadata_parser.get_format_instructions()}
    )
        
    # model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    model = ChatOpenAI(model="gpt-4.1")
    meta_extraction_chain = metadata_extract_template | model | case_metadata_parser
    case_metadata = meta_extraction_chain.invoke({"text":text_chunks[0]})
    print("===========Case metadata:", case_metadata)
    
    
    KG_extraction_parser = ListOfTriplesParser(NodeTriple)
    prompt_template = ChatPromptTemplate(
	    messages = [("system", KG_EXTRACTION_PROMPT), ("user", "{text}")],
        partial_variables={"format_instructions": KG_extraction_parser.get_format_instructions()}
    )
    # print(prompt_template)
    jsondata = []
    KG_extraction_chain = prompt_template | model

    prop_extraction_parser = JsonOutputParser(pydantic_object=NodeDictParser)
    prop_extract_template = PromptTemplate(
        template=PROP_EXTRACTION_PROMPT,
        partial_variables={"format_instructions": prop_extraction_parser.get_format_instructions()},
    )
    prop_extraction_chain = prop_extract_template | model | prop_extraction_parser
    
    count = 0
    context = ""
    previous_chunk_id = None
    nodes_and_rels = ""
    for text_chunk in text_chunks[0:10]:
        try:
            # Generate Response
            current_chunk_id = str(uuid.uuid4())
            resp = KG_extraction_chain.invoke({"text":text_chunk, "relevant_info_graph":nodes_and_rels, "metadata": case_metadata})
            # print(resp.content)
            triples = KG_extraction_parser.parse(resp.content)
            print(triples)
            print("=============================================================")
            # jsondata.append(json.loads(triples)["Data"])
            # Save Interaction
            # save_interaction(mem0_user_id, text_chunk, resp.content)
            context = triples
            for item in context:
                node1_type = item.node1_type
                node2_type = item.node2_type
                node1_value = item.node1_value
                node2_value = item.node2_value
                relationship = item.relationship
                resp = some_func_v2(driver, prop_extraction_chain, node1_type, node1_value, relationship, node2_type,  node2_value)
                if resp:
                    model_output = resp["model_output"]
                    print(model_output)
                    with driver.session() as session:
                        session.execute_write(merge_node, resp["node1_dict"]["labels"], model_output["node1_property"])
                        session.execute_write(merge_node, resp["node2_dict"]["labels"], model_output["node2_property"])
                        session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  model_output["node1_property"], resp["node2_dict"]["labels"], model_output["node2_property"], model_output["relationship"])
            
            
            with driver.session() as session:
                session.execute_write(merge_node, ["CourtCase"],{"hasCaseName":case_metadata["hasCaseName"], "hasCaseID":case_metadata["hasCaseID"]})
                session.execute_write(merge_node, ["Paragraph"],{"text":text_chunk,"chunk_id":current_chunk_id})
                session.execute_write(merge_relationship, ["CourtCase"],  {"hasCaseName":case_metadata["hasCaseName"], "hasCaseID":case_metadata["hasCaseID"]}, 
                                                        ["Paragraph"], {"text":text_chunk,"chunk_id":current_chunk_id},
                                                        "hasParagraph")
                
                
                if previous_chunk_id is not None:
                    session.execute_write(merge_relationship, ["Paragraph"],  {"chunk_id":previous_chunk_id}, 
                                                            ["Paragraph"], {"chunk_id":current_chunk_id},
                                                            "next")
                    
                    session.execute_write(merge_relationship, ["Paragraph"],  {"chunk_id":current_chunk_id}, 
                                                            ["Paragraph"], {"chunk_id":previous_chunk_id},
                                                            "previous")
            
            previous_chunk_id = current_chunk_id
            nodes_and_rels = get_graph(driver)
        except Exception as e:
            print(traceback.print_exc())
    
    

    create_vector_indices(driver, 768)
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
    create_all_node_embeddings(driver, embedding_model)

    
    
    
    
    # embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")

    # # The Neo4jVector Module will connect to Neo4j and create a vector index if needed.

    # db = Neo4jVector.from_texts(
    #     text_chunks, embeddings, url=uri, username=username, password=password
    # )

    # query = "What did the president say about Ketanji Brown Jackson"
    # docs_with_score = db.similarity_search_with_score(query, k=2)

    # # model = ChatOpenAI(temperature=0, model_name="gpt-4.1")
    # model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # mem0 = MemoryClient()
    # mem0_user_id = "legal_doc1"
    # # system_message =  KG_EXTRACTION_PROMPT
    # prompt_template = ChatPromptTemplate.from_messages(
	#     [("system", KG_EXTRACTION_PROMPT), ("system", "{relevant_info}"), ("user", "{text}")]
    # )
    # print(prompt_template)
    
    # jsondata = []
    # KG_extraction_chain = prompt_template | model


    # count = 0
    # for text_chunk in text_chunks:
    #     # retreive context
    #     context = retrieve_context(text_chunk, mem0_user_id)
    #     # Generate Response
    #     resp = KG_extraction_chain.invoke({"text":text_chunk, "relevant_info":context})
    #     jsondata.append(json.loads(resp.content)["Data"])

    #     # Save Interaction

    #     save_interaction(mem0_user_id, text_chunk, resp.content)
        
    
    
    # parser = JsonOutputParser(pydantic_object=node_dict_format)

    # prop_extract_template = PromptTemplate(
    # template=PROP_EXTRACTION_PROMPT,
    # partial_variables={"format_instructions": parser.get_format_instructions()},
    #     )

    # prop_extraction_chain = prop_extract_template | model | parser
    
    
        
    # for _json in jsondata:
    #     for item in _json:
            
    #         node1_type = item["node1_type"]
    #         node2_type = item["node2_type"]
    #         node1_value = item["node1_value"]
    #         node2_value = item["node2_value"]
    #         relationship = item["relationship"]
    #         # resp = some_func(node1_type, node1_value, relationship, node2_type,  node2_value)
    #         resp = some_func_v2(driver, prop_extraction_chain, node1_type, node1_value, relationship, node2_type,  node2_value)
    #         if not resp:
    #             continue
    #         model_output = resp["model_output"]
    #         print(model_output)
    #         with driver.session() as session:
    #             session.execute_write(merge_node, resp["node1_dict"]["labels"], model_output["node1_property"])
    #             session.execute_write(merge_node, resp["node2_dict"]["labels"], model_output["node2_property"])
    #             session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  model_output["node1_property"], resp["node2_dict"]["labels"], model_output["node2_property"], model_output["relationship"])
    # # break




    
    