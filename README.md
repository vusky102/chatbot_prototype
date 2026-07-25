# RAG Chatbot — Knowledge Assistant

A web-based internal assistant powered by Retrieval-Augmented Generation (RAG). It ingests approved PDF documents, indexes them in **Pinecone** (cloud hybrid search) or local **ChromaDB**, and generates grounded answers with source citations using OpenAI-compatible models.

---

## 🌟 Key Features

- **Dual Vector Database Architecture**:
  - **Pinecone (Cloud · Hybrid BM25+Dense)**: Combines dense vector embeddings with BM25 sparse keyword scores.
  - **ChromaDB (Local · Dense-Only)**: Zero-config local persistent store in `./chroma_db/`. Runs fully offline without cloud vector DB keys.
  - **Automatic Fallback (`auto` mode)**: Tries Pinecone first; if connection fails or API keys are missing, seamlessly falls back to ChromaDB.
- **Streamlit Web UI**: Chat interface, Admin management, and interactive 3D/2D embedding visualization pages.
- **PDF Ingestion & Visual Pipeline**: Heading-aware chunking, visual image extraction with spatial IDs for stable indexing, relative path storage for portable metadata, and automated Gemini visual captioning.
- **Image-Based Retrieval**: Perceptual visual search via average hash (`aHash`) matching.
- **Embedding Deduplication**: Query-time cosine similarity filtering to remove duplicate information across multiple documents.
- **Multi-Provider Models**: Flexible support for OpenAI, Google Gemini, and OpenRouter LLMs & Embeddings.
- **Voice Output**: Edge TTS text-to-speech integration for English and Vietnamese response vocalization.
- **Usage & Cost Monitoring**: Persistent token/cost history, CSV export, and a configurable warning threshold (`$9.00` in the current `budget_config.json`).
- **Model Evaluation**: Reference multiple-choice evaluation with configurable batching, up to 20 concurrent workers, timestamped accuracy history, and visible per-question/batch errors.

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
    chain.py                 Grounded answer generator + async usage callback
    eval_chain.py            Single-question and batch evaluation chains
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
    token_tracker.py         Persistent token and estimated-cost tracking
    budget.py                Cost-warning threshold management

  eval/
    eval_runner.py           Concurrent Q&A evaluation and result history

test/
  test_chroma_vector_store.py Unit tests for ChromaDB backend & factory logic

budget_config.json           Local warning threshold (currently $9.00)
usage_log.json               Persistent usage history
evaluation_results.csv       Timestamped evaluation answer columns
evaluation_results_metadata.json
                             Evaluation settings and accuracy history
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
  - Review/export usage and estimated cost, and configure the budget warning.
  - Run the Q&A evaluation with configurable range, batch size, and concurrency.
- **🌌 Visualize**: Interactive embedding space visualizations including 3D PCA Galaxy, 2D t-SNE scatter, and physics-based network graph views.

---

## 🧪 Testing

Run backend unit tests using `pytest`:

```bash
python -m pytest test/test_chroma_vector_store.py
```

---

## 📊 Evaluation and Cost Tracking

Open **Admin → 🧪 Evaluation** to run the reference multiple-choice question set. Every run appends a timestamped answer column to `evaluation_results.csv` and records the model, batch size, worker count, accuracy, and totals in `evaluation_results_metadata.json`. Failed questions are saved as `X`; the console reports the exception type and message for easier diagnosis.

The CLI runner is also available:

```bash
python scripts/evaluate_qa.py --batch-size 1 --start 1 --limit 100
```

The Admin UI supports up to 20 concurrent workers. Async LangChain callbacks record token usage from concurrent model calls in `usage_log.json`. **Admin → 📊 Usage & Cost** shows session/history totals and lets an administrator change the warning threshold stored in `budget_config.json`. This is an alert threshold, not a hard request limit.

---

## 📄 License

Internal Knowledge Assistant Prototype.
