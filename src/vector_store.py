from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams


EMBEDDING_PARAM = 768
class VectorDB:
    def __init__(self, client_url, embedding_model):
        self.client = QdrantClient(client_url)
        self.embedding_model = embedding_model
    
    def create_collection(self, coll_name)->QdrantVectorStore:
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
        