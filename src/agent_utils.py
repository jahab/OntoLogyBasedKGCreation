from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI
# from langgraph.runtime import Runtime
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

class KGBuilderState(TypedDict):
    doc_path: str
    messages: str | Dict
    case_metadata: Dict
    full_text: str
    text_chunks: str | None
    merge_node: str | None
    chunk: str
    previous_chunk_id: str | None
    nodes_and_rels: List
    
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


def extract_case_metadata_ag(state:KGBuilderState, config: RunnableConfig):
    case_metadata = extract_case_metadata(config["configurable"]["context"]["extraction_model"], state["chunk"])
    writer = get_stream_writer() 
    writer({"data": "Case Metdata Extracted", "type": "progress"}) 
    return {"case_metadata":case_metadata}

def get_models(provider: str, embedding_model: str, chat_model: str):
    provider = provider.lower()
    try:
        embedding_instance = EMBEDDING_MAP[provider](embedding_model)
        chat_instance = CHAT_MODEL_MAP[provider](chat_model)
        return embedding_instance, chat_instance
    except KeyError:
        raise ValueError(f"Unsupported provider: {provider}")


def init_context(data):
    
    load_dotenv()
    uri = "bolt://neo4j:7687"
    vector_db_uri = "http://vector_db:6333"
    os.environ["NEO4j_USER_NAME"] = os.getenv("NEO4j_USER_NAME")
    os.environ["NEO4j_PWD"] = os.getenv("NEO4j_PWD")
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["MEM0_API_KEY"] = os.getenv("MEM0_API_KEY")
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    
    # embedding_func = GoogleGenerativeAIEmbeddings
    # embedding_model = "models/text-embedding-004"
    # embedding_instance = embedding_func(model = embedding_model)
    # extraction_model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # extraction_model = ChatOpenAI(model="gpt-4.1")
    
    embedding_instance, extraction_model = get_models(data["provider"], data["embedding_model"], data["chat_model"])
    
    driver = GraphDatabase.driver(uri, auth=(os.environ["NEO4j_USER_NAME"], os.environ["NEO4j_PWD"]))
    vector_db = VectorDB(vector_db_uri,embedding_instance)
    vector_store = vector_db.create_collection("CourtCase")
    
    
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
    writer = get_stream_writer()
    writer({"data": "Initialised Context", "type": "progress"}) 
    return {"extraction_model":extraction_model,
            "embedding_model":embedding_instance, 
            "vector_store":vector_store, 
            "vector_db":vector_db,
            "neo4j_driver":driver,
            "KG_extraction_parser":KG_extraction_parser, 
            "KG_extraction_chain":KG_extraction_chain, 
            "prop_extraction_chain":prop_extraction_chain, 
            "prop_extraction_parser":prop_extraction_parser
            }


def extract_nodes_rels(state:KGBuilderState, config: RunnableConfig):
    nodes_and_rels = ""
    writer = get_stream_writer()
    try:
        # Generate Response
        writer({"data": "Extracting Node and rels", "type": "progress"}) 
        current_chunk_id = str(uuid.uuid4())
        resp = config["configurable"]["context"]["KG_extraction_chain"].invoke({"text":state["chunk"], "relevant_info_graph":state.get("nodes_and_rels",""), "metadata": state["case_metadata"]})
        # print(resp.content)
        triples = config["configurable"]["context"]["KG_extraction_parser"].parse(resp.content)
        # print(triples)
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
            try:
                resp = some_func_v2(config["configurable"]["context"]["neo4j_driver"], config["configurable"]["context"]["prop_extraction_chain"], node1_type, node1_value, relationship, node2_type,  node2_value)
                if resp:
                    model_output = resp["model_output"]
                    # print(model_output)
                    with state["neo4j_driver"].session() as session:
                        session.execute_write(merge_node, resp["node1_dict"]["labels"], model_output["node1_property"])
                        session.execute_write(merge_node, resp["node2_dict"]["labels"], model_output["node2_property"])
                        session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  model_output["node1_property"], resp["node2_dict"]["labels"], model_output["node2_property"], model_output["relationship"])
            except Exception as e:
                print(traceback.print_exc())
                print("----------------------------------------------------------------------------------")
                print("Node1: ", resp["node1_dict"]["labels"],  "  props:", model_output["node1_property"])
                print("Node2: ",  resp["node2_dict"]["labels"], "  props:", model_output["node2_property"])
                print("Relationship: ", model_output["relationship"])              
                            
        
        with state["neo4j_driver"].session() as session:
            session.execute_write(merge_node, ["CourtCase"],{"hasCaseName":state["case_metadata"]["hasCaseName"], "hasCaseID":state["case_metadata"]["hasCaseID"]})
            session.execute_write(merge_node, ["Paragraph"],{"text":state["chunk"],"chunk_id":current_chunk_id})
            session.execute_write(merge_relationship, ["CourtCase"],  {"hasCaseName":state["case_metadata"]["hasCaseName"], "hasCaseID":state["case_metadata"]["hasCaseID"]}, 
                                                        ["Paragraph"], {"text":state["chunk"],"chunk_id":current_chunk_id},
                                                        "hasParagraph")
            
            
            if state.get("previous_chunk_id",None) is not None:
                session.execute_write(merge_relationship, ["Paragraph"],  {"chunk_id":previous_chunk_id}, 
                                                        ["Paragraph"], {"chunk_id":current_chunk_id},
                                                        "next")
                
                session.execute_write(merge_relationship, ["Paragraph"],  {"chunk_id":current_chunk_id}, 
                                                        ["Paragraph"], {"chunk_id":previous_chunk_id},
                                                        "previous")
        
        previous_chunk_id = current_chunk_id
        records = get_graph(config["configurable"]["context"]["neo4j_driver"])
        nodes_and_rels  = []
        for res in records:
            if ":Paragraph" in res:
                continue
            nodes_and_rels.append(res)
        writer({"data": "Node and rels Extracted", "type": "progress"}) 
    except Exception as e:
        print(traceback.print_exc())
    return {"nodes_and_rels":nodes_and_rels, "previous_chunk_id":previous_chunk_id}




def refine_nodes(state:KGBuilderState, config: RunnableConfig):
    refine_nodes = RefineNodes(config["configurable"]["context"]["neo4j_driver"], config["configurable"]["context"]["vector_store"], config["configurable"]["context"]["extraction_model"])
    refine_nodes.refine_nodes()


def generate_embeddings(state:KGBuilderState, config: RunnableConfig):
    writer = get_stream_writer()
    writer({"data": "Generateing Embeddings", "type": "progress"}) 
    create_all_node_embeddings(config["configurable"]["context"]["neo4j_driver"], config["configurable"]["context"]["embedding_model"], config["configurable"]["context"]["vector_store"])
    writer({"data": "Embeddings Generated", "type": "progress"}) 

def read_document_ag(state:KGBuilderState, config: RunnableConfig):
    """
    Call to read a pdf and extract text as string from this pdf and return this text.
    """
    return {"full_text":read_document(state["doc_path"])}


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
    
    print(state.get("chunk_counter",0))

    if state.get("case_metadata",None) == None:    
        chunk = state["text_chunks"][state.get("chunk_counter",0)]
        return {"chunk":chunk, "chunk_counter":state.get("chunk_counter",0)+1, "next":"extract_case_metadata"}
    elif(state.get("case_metadata",None) and state["chunk_counter"]<=state["num_chunks"]-1):
        chunk = state["text_chunks"][state.get("chunk_counter",0)]
        return {"chunk":chunk, "chunk_counter":state.get("chunk_counter",0)+1, "next":"extract_nodes_rels"}
    elif state["chunk_counter"]==state["num_chunks"]:
        return {"next":"generate_embeddings"}