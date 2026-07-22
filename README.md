# RAG Chatbot — Knowledge Assistant

A web-based internal assistant powered by Retrieval-Augmented Generation (RAG). It ingests approved PDF documents, indexes them in **Pinecone** (cloud hybrid search) or local **ChromaDB**, and generates grounded answers with source citations using OpenAI-compatible models.

---

## 🌟 Key Features

- **Dual Vector Database Architecture**:
  - **Pinecone (Cloud · Hybrid BM25+Dense)**: Combines dense vector embeddings with BM25 sparse keyword scores.
  - **ChromaDB (Local · Dense-Only)**: Zero-config local persistent store in `./chroma_db/`. Runs fully offline without cloud vector DB keys.
  - **Automatic Fallback (`auto` mode)**: Tries Pinecone first; if connection fails or API keys are missing, seamlessly falls back to ChromaDB.
- **Streamlit Web UI**: Chat interface, Admin management, and interactive 3D/2D embedding visualization pages.
- **PDF Ingestion & Visual Pipeline**: Heading-aware chunking, visual image extraction, and automated Gemini visual captioning.
- **Image-Based Retrieval**: Perceptual visual search via average hash (`aHash`) matching.
- **Embedding Deduplication**: Query-time cosine similarity filtering to remove duplicate information across multiple documents.
- **Multi-Provider Models**: Flexible support for OpenAI, Google Gemini, and OpenRouter LLMs & Embeddings.
- **Voice Output**: Edge TTS text-to-speech integration for English and Vietnamese response vocalization.

---

## 🏗️ Architecture Overview

```text
app.py                       Streamlit entry point
src/
  config.py                  Environment-driven settings dataclass
  models.py                  Data models (DocumentChunk, SearchResult)
  vector_store_base.py       Abstract Base Class for Vector Store Backends
  vector_store.py            Pinecone Vector Store wrapper (cloud · hybrid BM25+dense)
  vector_store_chroma.py     ChromaDB Vector Store wrapper (local · dense-only)
  vector_store_factory.py    Factory for backend creation & automatic fallback
  tts.py                     Edge TTS text-to-speech service

  ingest/                    PDF Ingestion Pipeline
    pipeline.py              Orchestrator: parse → chunk → embed → upsert
    pdf_text_extraction.py   PyMuPDF / pypdf text extractor
    image_extraction.py      Visual element extractor (Gemini captioning)
    visual_caption.py        Image-to-text captioning service
    chunking.py              Heading-aware + recursive text splitters
    ahash.py                 Average perceptual hash for images

  lc/                        LangChain Integration Layer
    chain.py                 Grounded answer generator (LLM chain)
    retriever.py             LangChain retriever + dedup logic
    vectorstore.py           Backend-agnostic LangChain VectorStore adapter
    embeddings.py            Embedding model builder
    splitters.py             LangChain text splitter wrappers
    documents.py             Document ↔ SearchResult converters
    tools.py                 LangChain tool definitions

  rag/                       RAG Service Facade
    service.py               RAGService: retrieve + answer + image search
    retriever.py             Context formatting + dedup utilities

  ui/                        Streamlit Pages
    chat_page.py             Chat interface with image upload/paste
    admin_page.py            PDF ingestion, index management, DB backend selection, stats
    visualize_page.py        3D PCA, 2D t-SNE, and Network Graph
    styles.py                CSS injection for premium UI theming
    tuning.py                RAG parameter tuning sidebar & backend config
    rag_session.py           Cached session initialization

  utils/
    model_scanner.py         Multi-provider model discovery

test/
  test_chroma_vector_store.py Unit tests for ChromaDB backend & factory logic
```

---

## 💾 Vector Database Backends

| Backend | Storage Type | Retrieval Strategy | Requirements |
| :--- | :--- | :--- | :--- |
| **Pinecone** | Cloud Hosted | **Hybrid Search** (Dense embeddings + BM25 sparse keywords) | `PINECONE_API_KEY`, Cloud Index |
| **ChromaDB** | Local (`./chroma_db/`) | **Dense Semantic Search** (HNSW Cosine Distance) | None (Local execution) |

### Automatic Fallback Mechanism
When `vector_db_backend` is set to `"auto"` (default), the system attempts to connect to **Pinecone**. If `PINECONE_API_KEY` is not provided or the connection fails, it automatically switches to **ChromaDB** without interrupting application workflow.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.10+
- OpenAI-compatible API key (for embeddings and chat)
- *(Optional)* Pinecone API key (for cloud hybrid vector storage)
- *(Optional)* Gemini API key (for image extraction & visual captioning)

### 2. Environment Setup

```bash
# Clone repository
git clone <repository_url>
cd chat_bot_rag

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Copy `.env.example` to `.env` and fill in required values:

```bash
cp .env.example .env
```

At minimum, specify your OpenAI API key:
```ini
OPENAI_API_KEY=your_openai_api_key_here
# PINECONE_API_KEY is optional — if left blank, ChromaDB will be used locally!
```

### 4. Launch Application

```bash
python -m streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🖥️ Streamlit App Pages

- **💬 Chat**: Ask questions against the indexed knowledge base with interactive citations, multimodal image attachments, and Edge TTS audio responses.
- **⚙️ Admin**:
  - Ingest PDF documents with customizable chunk size, overlap, and strategies.
  - Dynamically switch between **Pinecone Cloud** and **ChromaDB Local** backends.
  - Monitor index vector stats and live ingestion terminal logs.
- **🌌 Visualize**: Interactive embedding space visualizations including 3D PCA Galaxy, 2D t-SNE scatter, and physics-based network graph views.

---

## 🧪 Testing

Run backend unit tests using `pytest`:

```bash
python -m pytest test/test_chroma_vector_store.py
```

---

## 📄 License

Internal Knowledge Assistant Prototype.
