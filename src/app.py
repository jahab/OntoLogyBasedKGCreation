from langchain_community.document_loaders import PyPDFLoader
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain.docstore.document import Document
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
from refine_nodes import *
import json

if __name__ == "__main__":
    load_dotenv()
    uri = "bolt://0.0.0.0:7687"
    vector_db_uri = "http://0.0.0.0:6333"
    os.environ["NEO4j_USER_NAME"] = os.getenv("NEO4j_USER_NAME")
    os.environ["NEO4j_PWD"] = os.getenv("NEO4j_PWD")
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
    os.environ["MEM0_API_KEY"] = os.getenv("MEM0_API_KEY")
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    driver = GraphDatabase.driver(uri, auth=(os.environ["NEO4j_USER_NAME"], os.environ["NEO4j_PWD"]))
    #import ontology
    load_ontology(driver)

    #create_constraint
    create_constraint(driver)
    create_index(driver)
    
    #read the Document
    file_path = ("35346_2009_39_1501_24473_Judgement_29-Oct-2020-1-2.pdf")
    text = read_document(file_path)
    doc =  Document(page_content=text, metadata={"source": "local"})
    
    text_chunks = chunk_pdf(text)
    
    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    # model = ChatOpenAI(model="gpt-4.1")
    
    
    
    
    KG_extraction_parser = ListOfTriplesParser(NodeTriple)
    prompt_template = ChatPromptTemplate(
	    messages = [("system", KG_EXTRACTION_PROMPT), ("user", "{text}")],
        partial_variables={"format_instructions": KG_extraction_parser.get_format_instructions()}
    )
    # print(prompt_template)
    
    KG_extraction_chain = prompt_template | model

    prop_extraction_parser = JsonOutputParser(pydantic_object=NodeDictParser)
    prop_extract_template = PromptTemplate(
        template=PROP_EXTRACTION_PROMPT,
        partial_variables={"format_instructions": prop_extraction_parser.get_format_instructions()},
    )
    prop_extraction_chain = prop_extract_template | model | prop_extraction_parser
    
    context = ""
    previous_chunk_id = None
    nodes_and_rels = ""
    
    case_metadata = extract_case_metadata(model,text_chunks[0])
    print("===========Case metadata:", case_metadata)
    
    for item in case_metadata:
        node1_type = item.node1_type
        node2_type = item.node2_type
        node1_value = item.node1_value
        node2_value = item.node2_value
        relationship = item.relationship
        try:
            resp = some_func_v2(driver, prop_extraction_chain, node1_type, node1_value, relationship, node2_type,  node2_value)
            if resp:
                model_output = resp["model_output"]
                # print(model_output)
                with driver.session() as session:
                    session.execute_write(merge_node, resp["node1_dict"]["labels"], model_output["node1_property"])
                    session.execute_write(merge_node, resp["node2_dict"]["labels"], model_output["node2_property"])
                    session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  model_output["node1_property"], resp["node2_dict"]["labels"], model_output["node2_property"], model_output["relationship"])
        except Exception as e:
            print(f"\n[app.py]: {traceback.format_exc()}")
            print("----------------------------------------------------------------------------------")
            print("Node1: ", resp["node1_dict"]["labels"],  "  props:", model_output["node1_property"])
            print("Node2: ",  resp["node2_dict"]["labels"], "  props:", model_output["node2_property"])
            print("Relationship: ", model_output["relationship"])              

    records = get_graph(driver)
    for res in records:
        if "Paragraph" in res["source_label"]  or "Paragraph" in res["target_labels"]:
            continue
        nodes_and_rels.append(res)
    nodes_and_rels =  format_triples(nodes_and_rels)
    
    
    for text_chunk in text_chunks:
        try:
            # Generate Response
            current_chunk_id = str(uuid.uuid4())
            resp = KG_extraction_chain.invoke({"text":text_chunk, "relevant_info_graph":nodes_and_rels, "metadata": json.dumps(case_metadata)})
            # print(resp.content)
            triples = KG_extraction_parser.parse(resp.content)
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
                    resp = some_func_v2(driver, prop_extraction_chain, node1_type, node1_value, relationship, node2_type,  node2_value)
                    if resp:
                        model_output = resp["model_output"]
                        # print(model_output)
                        with driver.session() as session:
                            session.execute_write(merge_node, resp["node1_dict"]["labels"], model_output["node1_property"])
                            session.execute_write(merge_node, resp["node2_dict"]["labels"], model_output["node2_property"])
                            session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  model_output["node1_property"], resp["node2_dict"]["labels"], model_output["node2_property"], model_output["relationship"])
                except Exception as e:
                    print(f"\n[app.py]: {traceback.format_exc()}")
                    print("----------------------------------------------------------------------------------")
                    print("Node1: ", resp["node1_dict"]["labels"],  "  props:", model_output["node1_property"])
                    print("Node2: ",  resp["node2_dict"]["labels"], "  props:", model_output["node2_property"])
                    print("Relationship: ", model_output["relationship"])              
                                
            
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
            records = get_graph(driver)
            nodes_and_rels  = []
            for res in records:
                if "Paragraph" in res["source_label"]  or "Paragraph" in res["target_labels"]:
                    continue
                nodes_and_rels.append(res)
            nodes_and_rels =  format_triples(nodes_and_rels)
        except Exception as e:
            print(f"\n[app.py]: {traceback.format_exc()}")

    

    embedding_func = GoogleGenerativeAIEmbeddings
    embedding_model = "models/text-embedding-004"
    embedding_instance = embedding_func(model = embedding_model)
    vector_db = VectorDB(vector_db_uri,embedding_instance)
    vector_store = vector_db.create_collection("CourtCase")
    # create_vector_indices(driver, 768)
    create_all_node_embeddings(driver, embedding_instance, vector_store)
    refine_nodes = RefineNodes(driver, vector_store, model)
    refine_nodes.refine_nodes()
    



    
    