from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer


from typing import Annotated
from typing_extensions import TypedDict
from dotenv import load_dotenv
from prompts import *
from typing import List, Dict, Literal, Any
from utils import *
import os
from output_parser import *
from neo4j import GraphDatabase
import uuid
import traceback
# from mem0 import MemoryClient
from refine_nodes import *
from vector_store import *
from global_import import *
import operator

class KGBuilderState(TypedDict):
    doc_path: str
    messages: str | Dict
    case_metadata: str | Dict
    full_text: str
    text_chunks: str | None
    merge_node: str | None
    chunk: str|None
    previous_chunk_id: str | None
    nodes_and_rels: List
    num_chunks : int
    chunk_counter : Annotated[int, operator.add]
    courtcase_details: Dict
    
class KGBuilderContext(TypedDict):
    neo4j_driver:Any
    vector_db: VectorDB
    vector_store: QdrantVectorStore
    extraction_model: Any
    embedding_model:Any
    KG_extraction_parser: Any
    KG_extraction_chain: Any
    prop_extraction_parser: Any
    prop_extraction_chain: Any

def human_node(state: KGBuilderState) -> Command[Literal["refine_nodes", "cancel"]]:
    is_approved = interrupt(
        {
            "question": "Would you like to merge the nodes?",
            # Surface the output that should be
            # reviewed and approved by the human.
            "llm_output": state["llm_output"]
        }
    )

    if is_approved:
        return Command(goto="refine_nodes")
    else:
        return Command(goto="cancel")



def init_context(data):    
    uri = "bolt://neo4j:7687"
    vector_db_uri = "http://vector_db:6333"
    neo4j_username = os.getenv("NEO4j_USER_NAME")
    neo4j_password = os.getenv("NEO4j_PWD")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    # embedding_func = GoogleGenerativeAIEmbeddings
    # embedding_model = "models/text-embedding-004"
    # embedding_instance = embedding_func(model = embedding_model)
    # extraction_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # extraction_model = ChatOpenAI(model="gpt-4.1")
    
    embedding_instance, extraction_model = get_models(data["model_provider"], data["embedding_provider"],data["embedding_model"], data["extraction_model"])
    
    driver = GraphDatabase.driver(uri, auth=(neo4j_username, neo4j_password))
    vector_db = VectorDB(vector_db_uri,embedding_instance)
    vector_store = vector_db.create_collection("CourtCase")
    # vector_store = vec_ins["vector_store"]
    # vec_cli = vec_ins["vector_client"]
    
    KG_extraction_parser = ListOfTriplesParser(NodeTriple)
    prompt_template = ChatPromptTemplate(
	    messages = [("system", KG_EXTRACTION_PROMPT), ("user", "{text}")],
        partial_variables={"format_instructions": KG_extraction_parser.get_format_instructions()}
    )
    
    prop_extraction_parser = JsonOutputParser(pydantic_object=NodeDictParser)
    
    prop_extract_template = PromptTemplate(
        template=PROP_EXTRACTION_PROMPT,
        partial_variables={"format_instructions": prop_extraction_parser.get_format_instructions()},
    )
    prop_extraction_chain = prop_extract_template | extraction_model | prop_extraction_parser
    KG_extraction_chain = prompt_template | extraction_model
    
    return {"extraction_model":extraction_model,
            "embedding_model":embedding_instance, 
            "vector_store":vector_store, 
            "vector_db_client":vector_db.client,
            "vector_db_collection_name":"CourtCase",
            "neo4j_driver":driver,
            "KG_extraction_parser":KG_extraction_parser, 
            "KG_extraction_chain":KG_extraction_chain, 
            "prop_extraction_chain":prop_extraction_chain, 
            "prop_extraction_parser":prop_extraction_parser,
            "username":data["username"]
            }



def extract_case_metadata_ag(state:KGBuilderState, config: RunnableConfig):
    case_metadata = extract_case_metadata(config["configurable"]["context"]["extraction_model"], state["chunk"])
    print(f"===========Case metadata: {case_metadata}")
    nodes_and_rels = []
    
    for item in case_metadata:
        node1_type = item.node1_type
        node2_type = item.node2_type
        node1_value = item.node1_value
        node2_value = item.node2_value
        relationship = item.relationship
        try:
            resp = some_func_v2(config["configurable"]["context"]["neo4j_driver"], config["configurable"]["context"]["prop_extraction_chain"], node1_type, node1_value, relationship, node2_type,  node2_value)
            if resp:
                model_output = resp["model_output"]
                with config["configurable"]["context"]["neo4j_driver"].session() as session:
                    session.execute_write(merge_node, resp["node1_dict"]["labels"], model_output["node1_property"])
                    session.execute_write(merge_node, resp["node2_dict"]["labels"], model_output["node2_property"])
                    session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  model_output["node1_property"], resp["node2_dict"]["labels"], model_output["node2_property"], model_output["relationship"])
        except Exception as e:
            print(f"[extract_case_metadata_ag]: {traceback.format_exc()}")
            print("----------------------------------------------------------------------------------")            

    records = get_graph(config["configurable"]["context"]["neo4j_driver"])
    for res in records:
        if "Paragraph" in res["source_labels"]  or "Paragraph" in res["target_labels"]:
            continue
        res["source_labels"], res["source_props"]
        nodes_and_rels.append(res)
    nodes_and_rels =  format_triples(nodes_and_rels)

    writer = get_stream_writer() 
    writer({"data": "Case Metdata Extracted", "type": "progress"}) 
    
    metadata_extract_template = ChatPromptTemplate(
            messages = [("system", METADATA_REFINE_PROMPT), ("user", "{text}")]
        )
    meta_extraction_chain = metadata_extract_template | config["configurable"]["context"]["extraction_model"]
    metadata =  meta_extraction_chain.invoke({"text": nodes_and_rels})
    case_meta_banner = """
                +-+-+-+-+ +-+-+-+-+-+-+-+-+
                |C|A|S|E| |M|E|T|A|D|A|T|A|
                +-+-+-+-+ +-+-+-+-+-+-+-+-+
    """
    print(case_meta_banner)
    print(metadata.content)
    case_metadata_parser = JsonOutputParser(pydantic_object=CaseMetadataParser)
    courtcase_extract_template = ChatPromptTemplate(
            messages = [("system", EXTRACT_COURTCASE_DETAILS_PROMPT), ("user", "{text}")],
            partial_variables={"format_instructions": case_metadata_parser.get_format_instructions()}
        )
    case_extraction_chain = courtcase_extract_template | config["configurable"]["context"]["extraction_model"] | case_metadata_parser
    case_extract =  case_extraction_chain.invoke({"text": state["chunk"]})
    print(f"case_extract : {case_extract}")
    return {"case_metadata":metadata.content, "nodes_and_rels": nodes_and_rels, "courtcase_details":case_extract}

def get_models(model_provider: str, embedding_provider:str, embedding_model: str, chat_model: str):
    model_provider = model_provider.lower()
    embedding_provider = embedding_provider.lower()
    try:
        if embedding_provider=="gemma" and embedding_model =="google/embeddinggemma-300M":
            import torch
            from sentence_transformers import SentenceTransformer
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_id = embedding_model #"google/embeddinggemma-300M"
            embedding_instance = SentenceTransformer(model_id).to(device=device)
        else:
            embedding_instance = EMBEDDING_MAP[embedding_provider](embedding_model)
    
        chat_instance = CHAT_MODEL_MAP[model_provider](chat_model)
        
        return embedding_instance, chat_instance
    except KeyError:
        raise ValueError(f"Unsupported provider: {traceback.format_exc()}")


def extract_nodes_rels(state:KGBuilderState, config: RunnableConfig):
    nodes_and_rels = ""
    writer = get_stream_writer()
    try:
        # Generate Response
        writer({"data": f"Extracting Node and rels for chunk number {state.get('chunk_counter',0)}/{state.get('num_chunks',0)}", "type": "progress"}) 
        current_chunk_id = str(uuid.uuid4())
        resp = config["configurable"]["context"]["KG_extraction_chain"].invoke({"text":state["chunk"], "relevant_info_graph":state.get("nodes_and_rels",""), "metadata": state["case_metadata"]})
        print(f"[extract_nodes_rels]: KG_EXTRACTION_CHAIN: \n{resp.content}")
        triples = config["configurable"]["context"]["KG_extraction_parser"].parse(resp.content)
        # print(triples)
        print("[extract_nodes_rels]: Create Paragraph\n")
        with config["configurable"]["context"]["neo4j_driver"].session() as session:
            print(f"STATE: {state}")
            
            session.execute_write(merge_node, ["CourtCase"],{"hasCaseName":state["courtcase_details"]["hasCaseName"], "hasCaseID":state["courtcase_details"]["hasCaseID"]})
            session.execute_write(merge_node, ["Paragraph"],{"text":state["chunk"],"chunk_id":current_chunk_id})
            session.execute_write(merge_relationship, ["CourtCase"],  {"hasCaseName":state["courtcase_details"]["hasCaseName"], "hasCaseID":state["courtcase_details"]["hasCaseID"]}, 
                                                        ["Paragraph"], {"text":state["chunk"],"chunk_id":current_chunk_id},
                                                        "hasParagraph")
            
            if state["chunk_counter"]==1:
                session.execute_write(merge_node, ["CaseMetadata"],{"text":state["case_metadata"]})
                session.execute_write(merge_relationship, ["CaseMetadata"],  {"text":state["case_metadata"]}, 
                                                            ["Paragraph"], {"text":state["chunk"],"chunk_id":current_chunk_id},
                                                            "hasCaseMetadata")
            
            print(f"======previous_chunk_id {state.get("previous_chunk_id",None)}")
            if state.get("previous_chunk_id",None) != None:
                print("================Connecting the chunk=================")
                session.execute_write(merge_relationship, ["Paragraph"],  {"chunk_id": state.get("previous_chunk_id")}, 
                                                        ["Paragraph"], {"chunk_id":current_chunk_id},
                                                        "next")
                
                session.execute_write(merge_relationship, ["Paragraph"],  {"chunk_id":current_chunk_id}, 
                                                        ["Paragraph"], {"chunk_id": state.get("previous_chunk_id")},
                                                        "previous")
        print("=============================================================")
        context = triples
        for item in context:
            node1_type = item.node1_type
            node2_type = item.node2_type
            node1_value = item.node1_value
            node2_value = item.node2_value
            relationship = item.relationship
            try:
                resp = some_func_v2(config["configurable"]["context"]["neo4j_driver"], config["configurable"]["context"]["prop_extraction_chain"], node1_type, node1_value, relationship, node2_type,  node2_value)
                if resp:
                    model_output = resp["model_output"]
                    # print(model_output)
                    with config["configurable"]["context"]["neo4j_driver"].session() as session:
                        session.execute_write(merge_node, resp["node1_dict"]["labels"], model_output["node1_property"])
                        session.execute_write(merge_node, resp["node2_dict"]["labels"], model_output["node2_property"])
                        session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  
                                                                  model_output["node1_property"], 
                                                                  resp["node2_dict"]["labels"], 
                                                                  model_output["node2_property"], 
                                                                  model_output["relationship"])
                        
                        session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  
                                                                  model_output["node1_property"], 
                                                                  ["Paragraph"], 
                                                                  {"text":state["chunk"],"chunk_id":current_chunk_id}, 
                                                                  "part_of")
                        
                        session.execute_write(merge_relationship, resp["node2_dict"]["labels"],  
                                                                  model_output["node2_property"], 
                                                                  ["Paragraph"], 
                                                                  {"text":state["chunk"],"chunk_id":current_chunk_id}, 
                                                                  "part_of")
            except Exception as e:
                print(f"\n[extract_nodes_rels]: {traceback.format_exc()}")
                print("----------------------------------------------------------------------------------")
                print(f"Node1: {resp["node1_dict"]["labels"]}, props: {model_output["node1_property"]}")
                print(f"Node2: {resp["node2_dict"]["labels"]}, props: { model_output["node2_property"]}")
                print(f"Relationship: {model_output["relationship"]}")
                                      
        previous_chunk_id = current_chunk_id
        records = get_graph(config["configurable"]["context"]["neo4j_driver"])
        nodes_and_rels  = []
        # print(f"records from get_graph {get_graph}")
        for rec in records:
            print(f"rec==== {rec}")
            if "Paragraph" in rec["source_labels"]  or "Paragraph" in rec["target_labels"]:
                continue
            nodes_and_rels.append(rec)
        writer({"data": f"Node and rels Extracted for chunk: {state.get('chunk_counter',0)}", "type": "progress"})
        
    except Exception as e:
        print(f"\n[extract_nodes_rels]: {traceback.format_exc()}")
        previous_chunk_id = None
    return {"nodes_and_rels":nodes_and_rels, "previous_chunk_id":previous_chunk_id}


def refine_nodes(state:KGBuilderState, config: RunnableConfig):
    refine_nodes = RefineNodes(config["configurable"]["context"]["neo4j_driver"],
                               config["configurable"]["context"]["vector_db_client"], 
                               config["configurable"]["context"]["vector_store"],
                               config["configurable"]["context"]["vector_db_collection_name"],
                               config["configurable"]["context"]["extraction_model"])
    user_collection = mongo_db["users"]
    user_details = user_collection.find_one({"username": config["configurable"]["context"]["username"]})
    refine_nodes.refine_nodes(task_id = user_details["task_id"])


def generate_embeddings(state:KGBuilderState, config: RunnableConfig):
    writer = get_stream_writer()
    writer({"data": "Generateing Embeddings", "type": "progress"}) 
    create_all_node_embeddings(config["configurable"]["context"]["neo4j_driver"], config["configurable"]["context"]["embedding_model"], config["configurable"]["context"]["vector_store"])
    writer({"data": "Embeddings Generated", "type": "progress"}) 

def read_document_ag(state:KGBuilderState, config: RunnableConfig):
    """
    Call to read a pdf and extract text as string from this pdf and return this text.
    """
    return {"full_text":read_document(state["doc_path"]), "case_metadata":{}, "courtcase_details":{}, "text_chunks":None,"merge_node":None,"chunk":None ,"previous_chunk_id":None,"nodes_and_rels":None,"num_chunks":0 }


def chunk_pdf_ag(state:KGBuilderState, config: RunnableConfig)->Dict:
    """
    Call to split a whole body of text in multiple chunks with overlap and return a list.
    """
    text_chunks = chunk_pdf(state["full_text"])
    return {"text_chunks":text_chunks, "chunk_counter":0, "num_chunks":len(text_chunks)}

def read_chunk_ag(state:KGBuilderState, config: RunnableConfig)->Dict:
    """
    yield next chunk.
    """
    writer = get_stream_writer()
    writer({"data": f"Reading chunk: {state.get('chunk_counter',0)}", "type": "progress"}) 
    
    print(f"chunk_counter:{state.get("chunk_counter",0)}")
    if state.get("case_metadata",None) == None:    
        chunk = state["text_chunks"][state.get("chunk_counter",0)]
        return {"chunk":chunk, "chunk_counter":1, "next":"extract_case_metadata"}
    elif(state.get("case_metadata",None) and state["chunk_counter"]<=state["num_chunks"]-1): #TODO FIXME: See if the last chunk gets read or not
        chunk = state["text_chunks"][state["chunk_counter"]]
        return {"chunk":chunk, "chunk_counter":1, "next":"extract_nodes_rels"}
    elif state["chunk_counter"]==state["num_chunks"]:
        return {"next":"generate_embeddings"}