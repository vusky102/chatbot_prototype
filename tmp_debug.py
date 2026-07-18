import sys
import os
sys.path.append(os.getcwd())
from src.config import Settings
from src.vector_store import PineconeVectorStore

settings = Settings.from_env()
vs = PineconeVectorStore(settings)
vs.connect()

with open('ahash_debug.txt', 'w', encoding='utf-8') as f:
    f.write(f'Connected. Stats: {vs.get_stats()}\n')
    for md in vs._iter_metadata(require_ahash=True):
        source = md.get('source_file')
        page = md.get('page')
        img_path = md.get('image_path')
        ahash = md.get('ahash')
        ctype = md.get('content_type')
        text = str(md.get('text'))[:50].replace('\n', ' ')
        f.write(f"{source} | Page: {page} | Img: {img_path} | AHash: {ahash} | Type: {ctype} | Text: {text}\n")
