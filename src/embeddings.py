from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams




client = QdrantClient("http://localhost:6333")
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