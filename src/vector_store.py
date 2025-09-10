from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams

# import torch
# from sentence_transformers import SentenceTransformer

# device = "cuda" if torch.cuda.is_available() else "cpu"
# model_id = "google/embeddinggemma-300M"

# model = SentenceTransformer(model_id).to(device=device)

EMBEDDING_PARAM = 768
class VectorDB:
    def __init__(self, client_url, embedding_model):
        self.client = QdrantClient(client_url)
        self.embedding_model = embedding_model
        self.collection_name = None
    
    def create_collection(self, coll_name)->QdrantVectorStore:
        self.collection_name = coll_name
        if not self.client.collection_exists(coll_name):
            self.client.create_collection(
                collection_name=coll_name,
                vectors_config=VectorParams(size=EMBEDDING_PARAM, distance=Distance.COSINE),
            )
        return QdrantVectorStore(
            client=self.client,
            collection_name=coll_name,
            embedding=self.embedding_model,
        )
        
    def generate_embeddings(self, sentences):
        # print(f"Device: {model.device}")
        # print(model)
        # print("Total number of parameters in the model:", sum([p.numel() for _, p in model.named_parameters()]))
        embeddings = self.embedding_model.encode(sentences)
        return embeddings

    def upload_embeddings(self, sentences, metadatas):
        embeddings = self.generate_embeddings(sentences)
        self.client.upsert(
            collection_name=self.collection_name,
            points=models.Batch(
                payloads = metadatas,
                vectors=[
                    embeddings
                ],
            ),
        )
        