import sys, os
from pathlib import Path
sys.path.append(os.getcwd())
from src.rag.service import RAGService
from src.ingest.visual_caption import VisualCaptioner

service = RAGService()
captioner = VisualCaptioner(service.settings.visual_provider)

# Get the caption
img_path = Path(r'output\rag_visuals\Public_035\page_6_diagram_1.png')
print("Describing image...")
desc = captioner.caption(img_path)
print("Caption generated:")
print(desc)
print("-" * 40)

# Simulate retrieval
print("Running semantic search...")
results = service.retrieve(desc)
for idx, r in enumerate(results):
    print(f"{idx+1}. Page {r.page} | Score {r.score:.4f} | ContentType: {r.content_type} | Text: {r.text[:100].replace(chr(10), ' ')}")
