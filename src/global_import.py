from  langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.chat_models import  ChatAnthropic
from sentence_transformers import SentenceTransformer
import enum
import pymongo
from dotenv import load_dotenv
load_dotenv()

EMBEDDING_MAP = {
    "openai": lambda model: OpenAIEmbeddings(model=model),
    "google": lambda model: GoogleGenerativeAIEmbeddings(model=model),
    "hugging_face": lambda model: HuggingFaceEmbeddings(model_name=model)
    
}

output_fixer_model = ChatGoogleGenerativeAI(model = "gemini-2.5-flash")

CHAT_MODEL_MAP = {
    "openai": lambda model: ChatOpenAI(model=model),
    "google": lambda model: ChatGoogleGenerativeAI(model=model),
    "anthropic": lambda model: ChatAnthropic(model=model),
}

USER_QUEUE = {"user_id": [], "task_id":[]} #TODO: FIXME: CRITICAL: Need a mutex on this queue other wise use mongo DB fro polling
RETRY_LIMIT = 3
myclient = pymongo.MongoClient("mongodb://mongodb:27017")
mongo_db = myclient["db"]