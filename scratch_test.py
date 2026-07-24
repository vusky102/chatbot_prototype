import json
import sys
sys.path.append('c:/Users/sonvu/Documents/Project/chat_bot_rag')
from src.models import DocumentChunk

data = json.load(open('c:/Users/sonvu/Documents/Project/chat_bot_rag/batch_jobs/9fcfc3d0-e226-40cd-8696-c92a3144658f/chunks.json', encoding='utf-8'))
print('Total chunks:', len(data))
max_meta = 0
max_text = 0
max_img = 0
max_raw_text = 0

for d in data:
    d.pop('_is_pending_visual', None)
    d.pop('_page_excerpt', None)
    chunk = DocumentChunk(**d)
    max_raw_text = max(max_raw_text, len(chunk.text.encode('utf-8')))
    max_img = max(max_img, len(chunk.image_path.encode('utf-8')))
    
    meta_size = len(json.dumps(chunk.metadata()).encode('utf-8'))
    max_meta = max(max_meta, meta_size)
    max_text = max(max_text, len(chunk.metadata()['text'].encode('utf-8')))

print(f'Max meta size: {max_meta}, Max raw text: {max_raw_text}, Max meta text: {max_text}, Max image: {max_img}')
