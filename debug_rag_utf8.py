import sys, os
sys.path.append(os.getcwd())
from src.rag.service import RAGService
service = RAGService()

with open("rag_out.txt", "w", encoding="utf-8") as f:
    f.write("Dumping Page 6 and 7 indexed records:\n")
    for md in service.retriever.vectorstore.store._iter_metadata(require_ahash=False):
        page = int(md.get('page', 0))
        if page in [6, 7]:
            f.write(f"Page {page} | Type: {md.get('content_type')} | Img: {md.get('image_path')} | Text: {str(md.get('text'))[:100]} | Hash: {md.get('ahash')}\n")

    f.write("\n--- Testing Search ---\n")
    query = "A graph illustrating the gradient descent algorithm with a parabola"
    results = service.retrieve(query)
    for idx, r in enumerate(results):
        f.write(f"{idx+1}. Page {r.page} | Score {r.score:.4f} | Img {r.image_path} | Text: {r.text[:100]}\n")
