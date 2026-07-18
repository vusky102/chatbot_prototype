import sys, os
sys.path.append(os.getcwd())
from src.rag.service import RAGService
service = RAGService()

# Find out what's on page 6 and 7 visually
print("Dumping Page 6 and 7 indexed records:")
for md in service.retriever.vectorstore.store._iter_metadata(require_ahash=False):
    page = int(md.get('page', 0))
    if page in [6, 7]:
        print(f"Page {page} | Type: {md.get('content_type')} | Img: {md.get('image_path')} | Text: {str(md.get('text'))[:100]} | Hash: {md.get('ahash')}")

# Run search for a sample query related to "gradient descent"
print("\n--- Testing Search ---")
query = "A graph illustrating the gradient descent algorithm with a parabola"
results = service.retrieve(query)
for idx, r in enumerate(results):
    print(f"{idx+1}. Page {r.page} | Score {r.score:.4f} | Img {r.image_path} | Text: {r.text[:100]}")
