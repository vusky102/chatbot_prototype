import os
from src.config import Settings
from src.vector_store import PineconeVectorStore

settings = Settings.from_env()
store = PineconeVectorStore(settings)
store.connect()

print("Connected!")
query_vector = [1e-5] * settings.embedding_dimension
response = store.index.query(
    vector=query_vector,
    top_k=10000,
    include_metadata=True,
    namespace=settings.pinecone_namespace,
    filter={"content_type": {"$in": ["image", "chart", "table", "figure"]}}
)

print(f"Found {len(response.matches)} matches")
for match in response.matches[:5]:
    print(match.metadata.get("content_type"), match.metadata.get("ahash"))
