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

from prompts import *
from typing import List
from utils import *
from dotenv import load_dotenv
import os
from output_parser import *
from neo4j import GraphDatabase



if __name__ == "__main__":
    load_dotenv()
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "admin@123"
    driver = GraphDatabase.driver(uri, auth=(username, password))
    #import ontology
    load_ontology(driver)
    #read the Document

    file_path = ("/mnt/c/Users/jafarhabshee/Downloads/Judgementsq/Judgements/Cases/35346_2009_39_1501_24473_Judgement_29-Oct-2020.pdf")
    loader = PyPDFLoader(file_path)
    pages = []
    text = ""

    for page in loader.lazy_load():
        pages.append(page)
        text = text+"\n"+page.page_content
    
    doc =  Document(page_content=text, metadata={"source": "local"})

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

    text_chunks = text_splitter.split_text(text)
    
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    model = ChatOpenAI(temperature=0, model_name="gpt-4.1")

    system_message =  KG_EXTRACTION_PROMPT
    prompt_template = ChatPromptTemplate.from_messages(
	    [("system", system_message), ("user", "{text}")]
    )
    print(prompt_template)
    
    jsondata = []
    KG_extraction_chain = prompt_template | model
    # chunk_resp = chain.invoke({"text":text_chunks[0]})

    for text_chunk in text_chunks:
        resp = KG_extraction_chain.invoke({"text":text_chunk})
        jsondata.append(json.loads(resp.content)["Data"])
    
    
    
    parser = JsonOutputParser(pydantic_object=node_dict_format)

    prop_extract_template = PromptTemplate(
    template=PROP_EXTRACTION_PROMPT,
    partial_variables={"format_instructions": parser.get_format_instructions()},
        )

    prop_extraction_chain = prop_extract_template | model | parser
    
    
        
    for _json in jsondata:
        for item in _json:
            
            node1_type = item["node1_type"]
            node2_type = item["node2_type"]
            node1_value = item["node1_value"]
            node2_value = item["node2_value"]
            relationship = item["relationship"]
            # resp = some_func(node1_type, node1_value, relationship, node2_type,  node2_value)
            resp = some_func_v2(driver, prop_extraction_chain, node1_type, node1_value, relationship, node2_type,  node2_value)
            if not resp:
                continue
            model_output = resp["model_output"]
            print(model_output)
            with driver.session() as session:
                session.execute_write(merge_node, resp["node1_dict"]["labels"], model_output["node1_property"])
                session.execute_write(merge_node, resp["node2_dict"]["labels"], model_output["node2_property"])
                session.execute_write(merge_relationship, resp["node1_dict"]["labels"],  model_output["node1_property"], resp["node2_dict"]["labels"], model_output["node2_property"], model_output["relationship"])
    # break




    
    