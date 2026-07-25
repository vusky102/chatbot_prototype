# RAG Chatbot Product Proposal
 
## Product Information
 
### Product Name
 
RAG Chatbot
 
### Team Name
 
Team 3
 
### Team Members
 
| Name | Account |
|---|---|
| Đỗ Đức Vinh | vinhdd5 |
| Lê Công Quốc Cường | CuongLCQ |
| Dư Xuân Lâm | lamdx |
| Hoàng Trịnh Dương | DuongHT8 |
| Nguyễn Anh Tuấn | TuanNA63 |
| Trần Thiện Dũng | DungTT120 |
| Cao Danh Huy | huyCD |
| Trần Văn Tú | tutv19 |
| Ngô Mạnh Linh | LinhNM49 |
| Vũ Sơn | Sonv2 |
| Nguyễn Vũ Hoài Nhân | nhannvh |
| Trần Văn Nam | NamTV12 |
 
### One-line Pitch
 
A general-purpose AI knowledge assistant that turns any collection of PDFs into a searchable text-and-image knowledge base with grounded answers, source citations, and measurable evaluation.
 
## Problem Statement
 
### Problem to Solve
 
Useful knowledge is often locked inside large and diverse PDF collections such as textbooks, research papers, technical manuals, regulations, reports, slide exports, and scanned visual documents. Finding an answer may require searching across many files, understanding different terminology, and manually inspecting pages, tables, diagrams, charts, or other images.

Conventional PDF search is primarily lexical and text-focused. It may miss semantically related passages, cannot reliably search visual content, and does not explain which evidence supports an answer. A reusable knowledge assistant should work with different PDF domains without requiring a domain-specific application rewrite, support both text and image queries, and provide a repeatable way to measure answer quality.
 
### People Affected
 
- Students and educators working with textbooks, lecture notes, and learning materials.
- Researchers and analysts searching papers, reports, tables, figures, and diagrams.
- Engineers and specialists consulting technical manuals, standards, and reference documents.
- Teams or individuals building domain-specific knowledge bases from their own PDFs.
- Knowledge-base operators who ingest documents, tune retrieval, and evaluate answer quality.
 
### Current Solutions and Limitations
 
- Manual document search is slow and depends on users knowing the correct file and terminology.
- Traditional keyword search may miss relevant passages that use different wording.
- Text-only tools overlook important information contained in figures, screenshots, charts, and diagrams.
- General-purpose AI assistants may answer from outside knowledge or invent details instead of grounding responses in the supplied PDFs.
- Without an evaluation system, retrieval and model changes are difficult to compare objectively.
 
## Proposed Solution
 
### Product Description
 
RAG Chatbot is a web-based, domain-agnostic knowledge assistant built with Streamlit and Retrieval-Augmented Generation (RAG). A user can build a knowledge base from any supported collection of PDFs. The ingestion pipeline extracts and chunks text, extracts visual elements with page-relative spatial identifiers, generates captions for those visuals, creates embeddings, and stores searchable vectors and metadata in Pinecone or local ChromaDB.
 
Users can ask a normal text question or provide an image as the query. Text questions use semantic retrieval, with hybrid BM25 and dense retrieval when Pinecone is active. Image queries use perceptual hashing for visual matching and image captioning to support semantic retrieval. The answer generator receives the retrieved text and visual descriptions, answers only from that evidence, and cites the source PDF and page. If the selected knowledge base does not contain enough information, it returns a clear not-found response.

An integrated evaluation system runs reference multiple-choice question sets with configurable ranges, batching, and concurrency. It records timestamped answers, accuracy, model settings, and run metadata so retrieval and generation changes can be measured over time.
 
### Value Provided
 
- Converts different PDF collections into searchable knowledge bases without domain-specific code changes.
- Finds relevant information by meaning as well as keywords.
- Makes charts, diagrams, screenshots, and other extracted PDF visuals searchable.
- Supports both text-based questions and image-based queries.
- Produces grounded answers with document, page, and heading citations.
- Measures model and retrieval quality through repeatable evaluation runs.
- Supports cloud-scale Pinecone retrieval and a local ChromaDB fallback.
 
### Differentiation
 
Unlike a general chatbot or basic PDF keyword search, RAG Chatbot combines multimodal PDF ingestion, semantic and hybrid retrieval, perceptual image matching, grounded answer generation, source traceability, and built-in evaluation. The same application can be repurposed for a new subject by replacing or extending the indexed PDF collection rather than changing the core application.
 
## Target Users
 
| User Group | Main Needs |
|---|---|
| Learners and educators | Ask grounded questions across textbooks, course notes, and educational PDFs. |
| Researchers and analysts | Search concepts, evidence, tables, figures, and citations across document collections. |
| Technical users | Find procedures and specifications in manuals, standards, and technical references. |
| Knowledge-base operators | Upload PDFs, choose a vector backend, manage sources, and tune retrieval settings. |
| Evaluators and developers | Run reference question sets, compare accuracy, inspect failures, and monitor cost. |
 
## Core Features
 
The current product includes:
 
1. Streamlit Chat, Admin, and Visualize interfaces.
2. General PDF ingestion with text extraction, chunking, and metadata preservation.
3. PDF visual extraction, spatial identification, caption generation, and portable relative-path metadata.
4. Text embeddings and configurable OpenAI-compatible generation models.
5. Pinecone hybrid dense/BM25 retrieval or local ChromaDB dense retrieval with automatic fallback.
6. Text-question answering grounded in retrieved PDF passages and visual captions.
7. Image-query retrieval using perceptual hashing and semantic image captions.
8. Source citations containing the document name, page, and available heading.
9. In-session chat memory and clear not-found behavior for unsupported questions.
10. Interactive embedding visualizations and retrieval diagnostics.
11. Persistent token and estimated-cost monitoring with a configurable warning threshold.
12. Reference Q&A evaluation with batching, concurrency controls, failure diagnostics, and timestamped accuracy history.
 
## AI Design
 
### AI Tasks
 
- Convert document chunks into vector embeddings.
- Extract meaningful visuals from PDF pages and describe them for semantic search.
- Compute perceptual hashes for matching image queries against indexed visuals.
- Convert each user question into an embedding for semantic search.
- Retrieve the most relevant document chunks from Pinecone or ChromaDB.
- Convert an uploaded query image into a caption and/or find visually similar indexed images.
- Generate an answer using only retrieved text and visual evidence.
- Preserve relevant source metadata for citation.
- Refuse to invent an answer when the retrieved context is insufficient.
- Evaluate answers against a reference set and preserve accuracy history.
 
### Supported AI Models
 
- **Generation:** OpenAI, Google Gemini, or OpenRouter chat models selected through configuration.
- **Embeddings:** An OpenAI-compatible embedding model selected through configuration.
- **Visual captioning:** A Gemini vision-capable model selected through configuration.
 
Exact model IDs are runtime-configurable through environment variables and the available model-selection controls; they are not hardcoded in the application.
 
### AI Workflow
 
```text
User provides a PDF knowledge base
                |
                v
 Extract text, metadata, and visuals
                |
        +-------+-------+
        |               |
        v               v
 Split text into    Caption and hash
 document chunks    extracted visuals
        |               |
        +-------+-------+
                |
                v
       Generate embeddings
                |
                v
Store vectors and metadata in Pinecone
       or local ChromaDB
                |
                v
 User asks with text or an image
                |
                v
 Retrieve relevant text and/or visuals
                |
                v
Generate an answer from retrieved context
                |
                v
 Display answer, images, and citations
                |
                v
 Evaluate against reference answers
```
 
## User Flow
 
1. A knowledge-base operator selects Pinecone, ChromaDB, or automatic backend selection.
2. The operator uploads one or more PDFs from the desired subject or domain.
3. The application extracts text and visuals, chunks the content, creates captions and hashes, generates embeddings, and indexes all metadata.
4. A user asks a text question or uploads/pastes an image in the Chat page.
5. The application performs semantic, hybrid, or visual retrieval as appropriate.
6. The configured model answers using only the retrieved PDF evidence.
7. Streamlit displays the answer with document and page citations and relevant visual results.
8. The conversation remains available in the current session for follow-up questions.
9. If the knowledge base lacks sufficient evidence, the application reports that the information could not be found.
10. An evaluator can run a reference question set in Admin and compare accuracy and failure history across configurations.
 
## Tech Stack
 
### Frontend
 
- Streamlit
 
### Backend
 
- Python
- LangChain for document loading, chunking, retrieval orchestration, and prompt composition
 
### Database
 
- Pinecone vector database for cloud hybrid dense/BM25 retrieval
- ChromaDB for local persistent dense retrieval and automatic fallback
- Streamlit session state for temporary conversation memory
 
### AI Framework/Tools
 
- OpenAI-compatible APIs for chat generation and embeddings
- Google Gemini for supported chat and visual-captioning workflows
- OpenRouter for additional configured chat models
- LangChain for the RAG pipeline
- PDF parsing library selected during implementation
- Async LangChain callbacks for persistent token and estimated-cost tracking
- Built-in evaluation runner for multiple-choice accuracy measurement
 
### Deployment
 
- Streamlit-compatible local or cloud deployment
- Optional Azure Virtual Machine deployment for a shared demonstration
- API credentials stored in environment variables rather than source control
 
The deployment target and provider configuration can vary by use case; the knowledge-base and retrieval behavior remain the same.
 
## MVP Scope
 
### Must Have
 
- Streamlit interface for chat, knowledge-base administration, usage monitoring, evaluation, and visualization.
- Ingestion of arbitrary supported PDF collections.
- Text parsing, heading-aware chunking, embedding, and dual-backend indexing.
- Visual extraction, captioning, perceptual hashing, and relative-path metadata.
- Text and image retrieval from indexed PDFs.
- Answers grounded in retrieved text and visual context.
- Supporting document and page citations.
- In-session chat memory.
- Clear response when requested information is not present.
- Evaluation runs with configurable range, batching, concurrency, and accuracy history.
 
### Nice to Have
 
- DOCX and TXT document support.
- Role-based access control.
- Persistent conversation history.
- User feedback collection.
- Automated regression alerts and comparative evaluation dashboards.
- Improved source previews and highlighted supporting passages.
- OCR enhancements for image-only or low-quality scanned PDFs.
 
## Current Progress
 
### Completed
 
- Terminal-based chatbot prototype (main.py).
- OpenAI-compatible API integration through environment configuration.
- Domain-agnostic knowledge-assistant role with strict grounding and citation instructions.
- In-session user and assistant message history.
- Streamlit web UI with Chat, Admin, and Visualize pages.
- Premium dark/light/system theme with glassmorphism styling.
- PDF ingestion pipeline (text + image extraction with Gemini captioning).
- Heading-aware and recursive document chunking.
- OpenAI embedding generation (text-embedding-3-small).
- Pinecone vector indexing with dotproduct metric.
- Hybrid search (dense embeddings + BM25 sparse keywords via pinecone-text).
- Embedding deduplication with configurable cosine threshold.
- LangChain RAG pipeline (retriever, grounded generator, tools).
- Source citation display with document name, page, and heading.
- Image-based retrieval via perceptual hashing (aHash + Hamming distance).
- Visual captioning for uploaded images to enhance semantic retrieval.
- Multi-provider model selection (OpenAI / Gemini / OpenRouter).
- Interactive 3D PCA, 2D t-SNE, and Network Graph embedding visualizations.
- Real-time terminal-style ingestion progress logs.
- Edge TTS voice output with English/Vietnamese language detection.
- Persistent usage logging with per-model token and estimated-cost breakdowns.
- Configurable cost-warning threshold stored in `budget_config.json` (currently `$9.00`).
- Admin Usage & Cost dashboard with history and CSV export.
- Multiple-choice evaluation UI with question range, batching, and up to 20 concurrent workers.
- Timestamped evaluation answer columns and metadata/accuracy history.
- Async-safe LangChain cost callback for concurrent evaluation calls.
- Per-question and per-batch exception diagnostics; failed answers are recorded as `X`.
 
### In Progress
 
- Evaluation analysis and retrieval/model tuning against the reference question set.
- Broader validation across PDF domains and visual-document types.
- Deployment hardening for shared environments.
 
### Blockers
 
- Final production hosting, access-control, and scaling requirements depend on the intended deployment environment.
 
## Success Criteria
 
The MVP will be considered successful when:
 
1. PDF collections from different knowledge domains can be processed and indexed without application changes.
2. Text questions retrieve relevant passages and produce answers grounded in those passages.
3. Image queries can find matching or semantically related PDF visuals and use their captions as answer context.
4. Generated answers display the supporting PDF name and page.
5. Questions not supported by the active knowledge base receive a clear not-found response rather than a fabricated answer.
6. Evaluation runs preserve answers, settings, accuracy, and failure information for comparison.
7. In-session follow-up questions retain the necessary conversation context.
 
The reference set currently contains 1,529 evaluated questions. The latest recorded run (`ai_answer_20260725_120724`) used GPT-4o-mini with 20 workers and achieved **73.38% accuracy (1,122/1,529)**. This is a baseline for tuning rather than the final acceptance threshold; no latency target has been finalized.
 
## Risks & Assumptions
 
| Risk or Assumption | Mitigation |
|---|---|
| PDF quality and structure vary significantly by source. | Use fallback text extractors, heading-aware chunking, spatial visual identifiers, and validate multiple document types. |
| The model may generate unsupported information. | Use a strict grounding prompt, require retrieved context, set a relevance threshold, and return a not-found response when evidence is insufficient. |
| Poor chunking or retrieval settings may return incomplete passages. | Test chunk size, overlap, retrieval count, metadata, and representative questions across different knowledge bases. |
| Visual extraction or captioning may misinterpret a figure. | Retain source-page metadata, combine hash and semantic retrieval, show the retrieved image, and evaluate representative visual questions. |
| OpenAI or Pinecone may be unavailable or incur unexpected cost. | Fall back to local ChromaDB when Pinecone is unavailable, report evaluation exceptions, monitor persistent usage, and configure a cost-warning threshold. |
| Uploaded PDFs may contain confidential or copyrighted information. | Ingest only authorized documents, avoid committing source files or credentials, and apply deployment-specific access controls. |
| Exact model and infrastructure settings are not finalized. | Keep these settings environment-driven and validate compatible choices before deployment. |
| Accuracy may vary across subjects, languages, and question styles. | Maintain diverse evaluation sets and compare timestamped results after model or retrieval changes. |
 
## Demo Scenario
 
1. The operator uploads a mixed PDF collection containing text, tables, figures, and diagrams.
2. The Admin page confirms that text chunks and visual elements have been indexed.
3. A user asks a text question whose answer appears in one of the PDFs.
4. The chatbot retrieves the relevant passage, answers, and cites the source PDF and page.
5. The user uploads or pastes an image taken from, or related to, an indexed PDF.
6. The chatbot finds the matching or semantically related visual and answers from its caption and surrounding document context.
7. The user asks a follow-up question to verify in-session context.
8. The user asks an unsupported question, and the chatbot returns a clear not-found response.
9. The evaluator runs the reference question set and reviews accuracy, failures, model settings, usage, and estimated cost.
 
## Delivery
 
- Deliver the application, configuration template, documentation, and evaluation artifacts.
- Publish the project to the designated source-control repository and deploy it to the selected local or cloud environment.

## Future Consideration

Evaluate an optional context-compression or summarization stage before answer generation. It may reduce token usage for large retrieval sets, but it must preserve citations and should only be adopted if the evaluation system shows that cost savings do not reduce answer accuracy.


## Actual Code Structure

```
chat_bot_rag/
│
├── .env                           # Environment variables (API keys, settings)
├── .env.example                   # Template with all supported env vars
├── .gitignore                     # Ignores .env, cache, output, media files
├── readme.txt                     # Full setup and usage documentation
├── requirements.txt               # All Python dependencies (organized by group)
│
├── app.py                         # Streamlit entry point (sidebar nav, routing)
├── main.py                        # Legacy terminal chatbot prototype
│
├── docs/                          # Project documentation
│   └── product_proposal.md        # This file
│
├── src/                           # Main application code
│   ├── __init__.py
│   ├── config.py                  # Settings dataclass from .env
│   ├── models.py                  # DocumentChunk, SearchResult data models
│   ├── vector_store.py            # Pinecone SDK wrapper (hybrid dense+BM25)
│   ├── vector_store_base.py       # Shared vector-store interface
│   ├── vector_store_chroma.py     # Local ChromaDB dense vector store
│   ├── vector_store_factory.py    # Backend selection and automatic fallback
│   ├── tts.py                     # Edge TTS voice output service
│   │
│   ├── ingest/                    # PDF ingestion pipeline
│   │   ├── pipeline.py            # Orchestrator: parse → chunk → embed → upsert
│   │   ├── pdf_text_extraction.py # PyMuPDF/pypdf text extraction
│   │   ├── image_extraction.py    # Visual element extraction from PDFs
│   │   ├── visual_caption.py      # Gemini image-to-text captioning
│   │   ├── chunking.py            # Heading-aware + recursive splitters
│   │   └── ahash.py               # Average perceptual hash for images
│   │
│   ├── lc/                        # LangChain integration layer
│   │   ├── chain.py               # Grounded answer generator (LLM chain)
│   │   ├── eval_chain.py          # Single/batched evaluation chains
│   │   ├── retriever.py           # LangChain retriever + dedup logic
│   │   ├── vectorstore.py         # Backend-agnostic LangChain adapter
│   │   ├── embeddings.py          # Embedding model builder
│   │   ├── splitters.py           # LangChain text splitter wrappers
│   │   ├── documents.py           # Document ↔ SearchResult converters
│   │   └── tools.py               # LangChain tool definitions
│   │
│   ├── rag/                       # RAG service facade
│   │   ├── service.py             # RAGService: retrieve + answer + image search
│   │   └── retriever.py           # Context formatting + dedup utilities
│   │
│   ├── ui/                        # Streamlit pages & styling
│   │   ├── chat_page.py           # Chat interface (text + image upload)
│   │   ├── admin_page.py          # PDF ingestion, index stats, source mgmt
│   │   ├── visualize_page.py      # 3D PCA, 2D t-SNE, Network Graph
│   │   ├── styles.py              # Premium CSS theming (glassmorphism)
│   │   ├── tuning.py              # RAG parameter tuning sidebar
│   │   └── rag_session.py         # Cached session initialization
│   │
│   ├── eval/
│   │   └── eval_runner.py         # Concurrent evaluation + accuracy history
│   │
│   └── utils/
│       ├── model_scanner.py       # Multi-provider model discovery
│       ├── token_tracker.py       # Usage and estimated-cost persistence
│       └── budget.py              # Warning-threshold management
│
├── scripts/
│   └── evaluate_qa.py             # Command-line evaluation runner
├── budget_config.json             # Local cost-warning threshold
├── usage_log.json                 # Persistent usage records
├── evaluation_results.csv         # Timestamped evaluation answers
├── evaluation_results_metadata.json # Evaluation settings and accuracy
│
└── test/                          # Tests
    ├── test_chroma_vector_store.py
    └── test_image_extract.py
```
