RAG Chatbot — Knowledge Assistant
====================================

A web-based internal assistant powered by Retrieval-Augmented Generation (RAG).
It ingests approved PDF documents, indexes them in Pinecone or local ChromaDB, and generates
grounded answers with source citations using OpenAI-compatible models.

The project includes:
- Streamlit web UI with Chat, Admin, and Visualize pages
- PDF ingestion pipeline with image extraction and visual captioning
- Dual Vector DB architecture (Pinecone cloud hybrid search & ChromaDB local dense search)
- Automatic database fallback (Pinecone -> ChromaDB when API key is missing or fails)
- Hybrid search (dense embeddings + BM25 sparse keywords via Pinecone)
- Embedding deduplication with cosine similarity
- Multi-provider model selection (OpenAI / Gemini / OpenRouter)
- Interactive 3D/2D embedding visualizations (Plotly + streamlit-agraph)
- Image-based retrieval via perceptual hashing (aHash)
- Edge TTS voice output with language detection
- LangChain-based RAG pipeline with strict grounding prompt


Architecture
------------

  app.py                       Streamlit entry point
  src/
    config.py                  Environment-driven settings (dataclass)
    models.py                  Data models (DocumentChunk, SearchResult)
    vector_store_base.py       Abstract base class for vector store backends
    vector_store.py            Native Pinecone SDK wrapper (cloud, hybrid BM25+dense)
    vector_store_chroma.py     Native ChromaDB wrapper (local, dense-only)
    vector_store_factory.py    Factory for backend selection & automatic fallback
    tts.py                     Edge TTS text-to-speech service

    ingest/                    PDF ingestion pipeline
      pipeline.py              Orchestrator: parse -> chunk -> embed -> upsert
      pdf_text_extraction.py   PyMuPDF / pypdf text extractor
      image_extraction.py      Visual element extractor (Gemini captioning)
      visual_caption.py        Image-to-text captioning service
      chunking.py              Heading-aware + recursive text splitters
      ahash.py                 Average perceptual hash for images

    lc/                        LangChain integration layer
      chain.py                 Grounded answer generator (LLM chain)
      retriever.py             LangChain retriever + dedup logic
      vectorstore.py           LangChain VectorStore adapter over vector store backends
      embeddings.py            Embedding model builder
      splitters.py             LangChain text splitter wrappers
      documents.py             Document <-> SearchResult converters
      tools.py                 LangChain tool definitions

    rag/                       RAG service facade
      service.py               RAGService: retrieve + answer + image search
      retriever.py             Context formatting + dedup utilities

    ui/                        Streamlit pages
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


Vector Database Backends
------------------------

The system supports a flexible dual-database architecture:

1. Pinecone (Cloud · Hybrid Search):
   - Combines dense vector embeddings with BM25 sparse keyword vectors.
   - Requires PINECONE_API_KEY and a cloud-hosted index.
   - Tunable hybrid search weighting via RAG_RETRIEVAL_HYBRID_ALPHA (0.0 = pure BM25, 1.0 = pure dense).

2. ChromaDB (Local · Dense-Only):
   - Embedded local vector database stored in `./chroma_db/`.
   - Uses HNSW cosine similarity distance.
   - Zero external cloud dependencies or API keys required for vector storage.
   - Supports aHash visual similarity search.

3. Automatic Fallback ("auto" mode):
   - Default mode on startup.
   - Attempts to initialize Pinecone if PINECONE_API_KEY is present.
   - Automatically falls back to local ChromaDB if Pinecone credentials are missing or connection fails.


Prerequisites
-------------

- Python 3.10 or newer
- pip
- An OpenAI-compatible API key (embeddings + chat)
- (Optional) A Pinecone API key for cloud hybrid search
- (Optional) Gemini API key for visual captioning
- (Optional) OpenRouter API key for fallback/free models
- Internet access for Edge TTS voice synthesis


Quick Start
-----------

1. Clone the repository and enter the project directory.

2. Create and activate a virtual environment:

   Windows PowerShell:
     py -m venv .venv
     .venv\Scripts\Activate.ps1

   macOS / Linux:
     python3 -m venv .venv
     source .venv/bin/activate

3. Install dependencies:

     pip install -r requirements.txt

4. Create a .env file from the template:

     copy .env.example .env          # Windows
     cp .env.example .env            # macOS / Linux

   Fill in at minimum:
     - OPENAI_API_KEY
     - PINECONE_API_KEY (optional; automatically falls back to ChromaDB if omitted)

5. Run the Streamlit app:

     python -m streamlit run app.py

   Open http://localhost:8501 in your browser.


Environment Variables
---------------------

See .env.example for all supported settings. Key groups:

  Primary OpenAI-Compatible Client
    OPENAI_API_KEY, OPENAI_API_BASEURL, OPENAI_API_MODEL

  Embedding Configuration
    OPENAI_EMBEDDING_API_KEY, OPENAI_EMBEDDING_BASEURL,
    OPENAI_EMBEDDING_MODEL, OPENAI_EMBEDDING_DIMENSION

  Vector Database Backends
    PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_NAMESPACE,
    PINECONE_CLOUD, PINECONE_REGION

  RAG Pipeline Tuning
    RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP, RAG_CHUNK_STRATEGY,
    RAG_RETRIEVAL_TOP_K, RAG_RETRIEVAL_SCORE_THRESHOLD,
    RAG_RETRIEVAL_DEDUP_ENABLED, RAG_RETRIEVAL_DEDUP_THRESHOLD,
    RAG_RETRIEVAL_CANDIDATE_MULTIPLIER, RAG_RETRIEVAL_HYBRID_ALPHA

  Visual Extraction & Captioning
    RAG_VISUAL_PROVIDER, RAG_VISUAL_OUTPUT_DIR,
    GEMINI_API_KEY, GEMINI_MODEL

  OpenRouter Fallback
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_API_MODEL

  Text-To-Speech
    TTS_ENABLED, TTS_AUTOPLAY, TTS_DEFAULT_LANGUAGE,
    TTS_AUDIO_DIR, TTS_VOICE_POSITION_ENG, TTS_VOICE_POSITION_VIE


Streamlit Pages
---------------

  Chat      -- Ask questions against the indexed knowledge base.
               Supports text input, image upload/paste, and voice output.
               Answers include source citations with document name and page.

  Admin     -- Upload and ingest PDFs into Pinecone or ChromaDB.
               Select active Database Backend (Pinecone Cloud vs local ChromaDB).
               View index statistics, manage source files, and monitor
               ingestion progress with real-time terminal-style logs.

  Visualize -- Search and explore embedding relationships.
               - 3D PCA Galaxy View (Plotly interactive 3D scatter)
               - 2D t-SNE Scatter (Plotly interactive 2D scatter)
               - Network Graph (streamlit-agraph physics-based nodes)
               Shows top matches with similarity scores in the sidebar.


Testing
-------

Run unit tests using pytest:

  python -m pytest test/test_chroma_vector_store.py


Terminal CLI (Legacy)
---------------------

The original terminal prototype is still available in main.py:

  python main.py

This runs a command-line chatbot with in-session history and Edge TTS.
It uses a small in-memory knowledge base.


Text-To-Speech
--------------

Edge TTS converts assistant responses to spoken audio using Microsoft's
online neural voice service. No API key is required.

  English voices:
    0  en-US-AriaNeural          Female
    1  en-US-JennyNeural         Female
    2  en-US-GuyNeural           Male
    3  en-US-ChristopherNeural   Male

  Vietnamese voices:
    0  vi-VN-HoaiMyNeural        Female
    1  vi-VN-NamMinhNeural       Male

Configure with TTS_VOICE_POSITION_ENG and TTS_VOICE_POSITION_VIE.
Set TTS_ENABLED=false to disable audio entirely.


Troubleshooting
---------------

  ModuleNotFoundError
    Activate the virtual environment and run:
    pip install -r requirements.txt

  Missing environment variables
    Confirm .env exists and contains at minimum OPENAI_API_KEY.
    Copy from .env.example if needed.

  Authentication error
    Verify your API keys are valid for the configured providers.

  Pinecone dimension mismatch
    Ensure OPENAI_EMBEDDING_DIMENSION matches your Pinecone index
    dimension. Default is 1536 for text-embedding-3-small.

  ChromaDB storage location
    ChromaDB stores persistent data locally in `./chroma_db/`. Delete this
    folder if you need to reset the local store completely.

  TTS not playing
    Confirm TTS_ENABLED=true and TTS_AUTOPLAY=true. Edge TTS
    requires an active internet connection.

  Visualize page error
    Ensure plotly, scikit-learn, scipy, and streamlit-agraph
    are installed. Run pip install -r requirements.txt.
