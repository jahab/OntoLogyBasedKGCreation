from  langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.chat_models import  ChatAnthropic
import enum


EMBEDDING_MAP = {
    "openai": lambda model: OpenAIEmbeddings(model=model),
    "google": lambda model: GoogleGenerativeAIEmbeddings(model=model),
}

CHAT_MODEL_MAP = {
    "openai": lambda model: ChatOpenAI(model=model),
    "google": lambda model: ChatGoogleGenerativeAI(model=model),
    "anthropic": lambda model: ChatAnthropic(model=model),
    # Add more providers like "cohere", "mistral", etc. as needed
}


