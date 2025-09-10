from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

import torch
from sentence_transformers import SentenceTransformer


device = "cuda" if torch.cuda.is_available() else "cpu"
model_id = "google/embeddinggemma-300M"
model = SentenceTransformer(model_id).to(device=device)

client = QdrantClient("http://vector_db:6333")
embedding_model = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
EMBEDDING_PARAM = 768
client.create_collection(
    collection_name="CourtCase_collection",
    vectors_config=VectorParams(size=EMBEDDING_PARAM, distance=Distance.COSINE),
)

vector_store = QdrantVectorStore(
    client=client,
    collection_name="CourtCase_collection",
    embedding=embedding_model,
)

def generate_embeddings(sentences):
    # print(f"Device: {model.device}")
    # print(model)
    # print("Total number of parameters in the model:", sum([p.numel() for _, p in model.named_parameters()]))
    embeddings = model.encode(sentences)
    return embeddings