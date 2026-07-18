import sys, os
from pathlib import Path
sys.path.append(os.getcwd())
from src.rag.service import RAGService
from src.ingest.visual_caption import VisualCaptioner

service = RAGService()
captioner = VisualCaptioner(service.settings.visual_provider)

# Get the caption
img_path = Path(r'output\rag_visuals\Public_035\page_6_diagram_1.png')
desc = captioner.caption(img_path)

with open("sim_out.txt", "w", encoding="utf-8") as f:
    f.write("Caption generated:\n")
    f.write(desc + "\n")
    f.write("-" * 40 + "\n")

    # Simulate retrieval
    f.write("Running semantic search...\n")
    results = service.retrieve(desc)
    for idx, r in enumerate(results):
        f.write(f"{idx+1}. Page {r.page} | Score {r.score:.4f} | ContentType: {r.content_type} | Text: {r.text[:100].replace(chr(10), ' ')}\n")
