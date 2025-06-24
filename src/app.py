from langchain_community.document_loaders import PyPDFLoader
from langchain_community.graphs.graph_document import GraphDocument
from langchain_core.documents import Document
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain.docstore.document import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

import prompts
from typing import List
from utils import *
from dotenv import load_dotenv
import os

from neo4j import GraphDatabase




if __name__ == "__main__":
    
    uri = "bolt://localhost:7687"
    username = "neo4j"
    password = "admin@123"
    driver = GraphDatabase.driver(uri, auth=(username, password))
    #import ontology
    with driver.session() as session:
        edges = session.execute_read(get_ontology_in_graph)
    
    #read the Document

    file_path = ("/mnt/c/Users/jafarhabshee/Downloads/Judgementsq/Judgements/Cases/35346_2009_39_1501_24473_Judgement_29-Oct-2020.pdf")
    loader = PyPDFLoader(file_path)
    pages = []
    text = ""

    for page in loader.alazy_load():
        pages.append(page)
        text = text+"\n"+page.page_content
    
    doc =  Document(page_content=text, metadata={"source": "local"})

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)

    text_chunks = text_splitter.split_text(text)
 
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

    model = ChatOpenAI(temperature=0, model_name="gpt-4.1")

    system_message =  prompts.KG_EXTRACTION_PROMPT
    prompt_template = ChatPromptTemplate.from_messages(
	    [("system", system_message), ("user", "{text}")]
    )
    print(prompt_template)
    
    jsondata = []
    chain = prompt_template | model
    for text_chunk in text_chunks:
        resp = chain.invoke({"text":text_chunk})
        jsondata.append(resp.content)
    




    
    