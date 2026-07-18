## RAG backend (LangChain stages 1–4)

Pinecone RAG libraries live under `src/`. CLI tools live under `scripts/`.
Visual ingest stores an `ahash` metadata field on captioned image chunks for
hash-based lookup.

This branch wires LangChain into the production path while keeping workshop
facades (`DocumentChunk`, `SearchResult`, `RAGService`, Streamlit UI):

| Stage | LangChain piece | Workshop adapter |
|-------|-----------------|------------------|
| 1 | `RecursiveCharacterTextSplitter` | `src/lc/splitters.py` → `chunk_extracted_text` |
| 2 | `OpenAIEmbeddings` + `VectorStore` | `src/lc/embeddings.py`, `LangChainPineconeVectorStore` |
| 3 | `BaseRetriever` | `LangChainSemanticRetriever` (score threshold + dedup) |
| 4 | LCEL `prompt \| llm \| parser` | `LangChainGroundedGenerator` |

Python 3.14 cannot install `langchain-pinecone` yet, so Pinecone stays on the
existing SDK behind a LangChain `VectorStore` adapter (`src/vector_store.py` +
`src/lc/vectorstore.py`).

`main.py` uses Pinecone via LangChain `@tool` + `bind_tools`:
`retrieve_knowledge` → `RAGService`.
Streamlit (`app.py`) uses the same `RAGService` for Chat and Admin.

TTS lives in `src/tts.py` (shared by CLI and Chat speaker icons).

### Layout

```text
src/
├── config.py
├── models.py
├── tts.py             # Edge TTS (CLI + Chat UI)
├── vector_store.py    # Pinecone SDK client
├── lc/                # LangChain stages 1–4
│   ├── splitters.py
│   ├── embeddings.py
│   ├── vectorstore.py
│   ├── retriever.py
│   ├── chain.py
│   ├── tools.py           # @tool retrieve_knowledge (CLI)
│   └── documents.py
├── ingest/            # text + visual → chunks (+ aHash)
├── rag/               # RAGService + retrieve helpers
└── ui/                # Streamlit chat + admin pages

scripts/
├── ingest_pdfs.py     # CLI ingest → Pinecone
└── rag_cli.py         # CLI search / ask / chat / stats

app.py                 # Streamlit UI (Chat + Admin)
main.py                # CLI chatbot: LangChain @tool → RAGService
```

### Setup

```powershell
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`. At minimum ensure:

```text
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=rag-chatbot
PINECONE_NAMESPACE=training-gd4
OPENAI_API_KEY=your-key
OPENAI_API_BASEURL=https://api.openai.com/v1
OPENAI_API_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_API_KEY=your-embedding-enabled-key
OPENAI_EMBEDDING_BASEURL=https://api.openai.com/v1
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_EMBEDDING_DIMENSION=1536
```

`OPENAI_EMBEDDING_*` falls back to `OPENAI_API_*` when empty.

### Ingest

```powershell
py scripts\ingest_pdfs.py --pdf docs\Training_data_GD4\input\Public_035.pdf --no-visuals
py scripts\ingest_pdfs.py --pdf docs\Training_data_GD4\input\Public_035.pdf --strategy page
py scripts\ingest_pdfs.py --dir docs\Training_data_GD4\input --limit 10
```

Chunk strategies (`RAG_CHUNK_STRATEGY` / `--strategy`):
`heading` (default), `page`, `fixed`, `paragraph`.

Visual failures (Gemini quota/model errors) no longer abort ingest: text is
still indexed, and extracted images fall back to page-context embeddings + aHash.

### Query / chat

```powershell
streamlit run app.py
py scripts\rag_cli.py --search "Công thức hồi quy tuyến tính là gì?"
py scripts\rag_cli.py --ask "Gradient descent dùng để làm gì?"
py scripts\rag_cli.py --image-search path\to\screenshot.png
py scripts\rag_cli.py --stats
py scripts\rag_cli.py
py main.py
```

Streamlit UI:
- **Chat** — Q&A with source citations; speaker icon on bubbles plays Edge TTS
- **Admin** — stats, PDF ingest, delete source, retrieval tuning/debug

### Run unit tests

```powershell
py -m unittest test.test_rag_backend test.test_tenacity
```

### Query-time dedup

Semantic retrieval fetches `TOP_K * CANDIDATE_MULTIPLIER` candidates, then keeps
only results whose embeddings are sufficiently different (cosine distance >=
threshold). This reduces near-duplicate chunks before the LLM sees them.

```text
RAG_RETRIEVAL_DEDUP_ENABLED=true
RAG_RETRIEVAL_DEDUP_THRESHOLD=0.05
RAG_RETRIEVAL_CANDIDATE_MULTIPLIER=3
```

Lower `DEDUP_THRESHOLD` is stricter about calling two chunks duplicates.

### Coming next

- Evaluation set + batch ingest tuning
- Optional `langchain-pinecone` once Python wheels support 3.14
