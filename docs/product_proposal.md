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
 
An AI-powered internal company assistant that retrieves reliable answers from approved documents and shows the supporting sources.
 
## Problem Statement
 
### Problem to Solve
 
Company knowledge is often distributed across employee handbooks, HR policies, onboarding guides, IT manuals, and FAQ documents. Employees spend time searching through these files or repeatedly asking HR and IT teams for the same information.
 
### People Affected
 
- Employees who need quick answers about policies, leave, onboarding, and IT support.
- New employees who need guidance during onboarding.
- HR and IT teams that repeatedly answer common questions.
- Administrators responsible for maintaining internal documentation.
 
### Current Solutions and Limitations
 
- Manual document search is slow and depends on users knowing the correct file and terminology.
- Traditional keyword search may miss relevant passages that use different wording.
- Direct questions to HR or IT create repetitive support work and delayed responses.
- General-purpose AI assistants may invent answers when they do not have access to approved company information.
 
## Proposed Solution
 
### Product Description
 
RAG Chatbot is a web-based internal assistant built with Streamlit and Retrieval-Augmented Generation (RAG). It processes approved PDF documents, converts their content into embeddings, stores them in Pinecone, retrieves relevant passages for each question, and asks an OpenAI model to answer using only that retrieved context.
 
The response includes the supporting document source. If the knowledge base does not contain enough information, the chatbot states that the answer could not be found instead of inventing a company policy.
 
### Value Provided
 
- Reduces the time employees spend searching for internal information.
- Reduces repetitive HR and IT support requests.
- Produces consistent answers grounded in approved documents.
- Improves onboarding and employee self-service.
- Makes the origin of each answer visible through source citations.
 
### Differentiation
 
Unlike a general chatbot or basic keyword search, RAG Chatbot uses semantic retrieval over approved company documents and generates an answer from the retrieved passages. It is designed to provide traceable answers, cite sources, and explicitly reject unsupported questions.
 
## Target Users
 
| User Group | Main Needs |
|---|---|
| Employees | Find accurate policies, procedures, leave information, and common IT guidance quickly. |
| New employees | Access onboarding steps, required documents, account setup, training, and first-day guidance. |
| HR and IT teams | Reduce repetitive questions and direct employees to consistent information. |
| Knowledge administrators | Supply approved PDF documents and keep the searchable knowledge base current. |
| Reviewers/demo users | Verify that answers are correctly retrieved from the provided mock documents. |
 
## Core Features
 
The MVP will include:
 
1. Password-protected Streamlit chat interface.
2. PDF document ingestion and text extraction.
3. Document chunking and metadata preservation.
4. OpenAI embedding generation.
5. Pinecone vector indexing and semantic retrieval.
6. Answers grounded only in retrieved document context.
7. Document source citations with each supported answer.
8. In-session chat memory.
9. Clear fallback when relevant information is not found.
10. Error handling for document processing, retrieval, and AI service failures.
 
## AI Design
 
### AI Tasks
 
- Convert document chunks into vector embeddings.
- Convert each user question into an embedding for semantic search.
- Retrieve the most relevant document chunks from Pinecone.
- Generate a concise answer using only the retrieved context.
- Preserve relevant source metadata for citation.
- Refuse to invent an answer when the retrieved context is insufficient.
 
### Planned AI Models
 
- **Generation:** An OpenAI chat model, configured through environment variables.
- **Embeddings:** An OpenAI embedding model, configured through environment variables.
 
Exact model IDs will be finalized during implementation based on project access and compatibility. They will not be hardcoded in the application.
 
### AI Workflow
 
```text
Administrator provides approved PDFs
                |
                v
       Parse and clean text
                |
                v
     Split text into document chunks
                |
                v
Generate embeddings with OpenAI
                |
                v
Store vectors and metadata in Pinecone
                |
                v
        Employee asks a question
                |
                v
Retrieve relevant chunks from Pinecone
                |
                v
Generate an answer from retrieved context
                |
                v
Display answer and sources in Streamlit
```
 
## User Flow
 
1. An administrator supplies the approved mock PDF documents.
2. The application extracts, chunks, embeds, and indexes the document content in Pinecone.
3. A user opens the Streamlit application through the Azure VM public IP.
4. The user enters the demo password.
5. The user asks a question about the indexed documents.
6. The application retrieves the most relevant document chunks.
7. The OpenAI model generates an answer using only the retrieved context.
8. Streamlit displays the answer and its supporting source.
9. The conversation remains available in the current session for follow-up questions.
10. If no relevant content is found, the application reports that the information is unavailable in the knowledge base.
 
## Tech Stack
 
### Frontend
 
- Streamlit
 
### Backend
 
- Python
- LangChain for document loading, chunking, retrieval orchestration, and prompt composition
 
### Database
 
- Pinecone vector database for embeddings and document metadata
- Streamlit session state for temporary conversation memory
 
### AI Framework/Tools
 
- OpenAI API for chat generation and embeddings
- LangChain for the RAG pipeline
- PDF parsing library selected during implementation
 
### Deployment
 
- Azure Virtual Machine
- Streamlit exposed through the VM public IP in test mode
- Streamlit password protection for demo access
- API credentials and passwords stored in environment variables rather than source control
 
The exact VM specification, network configuration, and OpenAI/Pinecone configuration will be finalized before deployment.
 
## MVP Scope
 
### Must Have
 
- Streamlit password-protected chat interface.
- Ingestion of the mock PDF documents provided by Hieu.
- PDF parsing, chunking, embedding, and Pinecone indexing.
- Semantic retrieval of information from indexed PDFs.
- Answers grounded in retrieved content.
- Supporting source citations.
- In-session chat memory.
- Clear response when requested information is not present.
- Azure VM test deployment accessible through a public IP.
 
### Nice to Have
 
- DOCX and TXT document support.
- Role-based access control.
- Persistent conversation history.
- Administrative document upload and index management.
- User feedback collection.
- Automated retrieval-quality evaluation.
- Improved source previews and highlighted supporting passages.
 
## Current Progress
 
### Completed
 
- Terminal-based chatbot prototype.
- OpenAI-compatible API integration through environment configuration.
- Internal-assistant system role and response instructions.
- In-session user and assistant message history.
- Prototype in-memory knowledge base with keyword matching.
 
The keyword matcher is an early retrieval prototype. It is not yet a Pinecone-based RAG implementation.
 
### In Progress
 
- Streamlit user interface.
- PDF ingestion and processing.
- OpenAI embedding integration.
- Pinecone indexing and semantic retrieval.
- LangChain RAG workflow.
- Source citation display.
- Streamlit password protection.
- Azure VM test deployment.
 
### Blockers
 
- The team is waiting for Hieu to provide mock PDF documents for ingestion, retrieval testing, and the final demo.
- Exact OpenAI model IDs, Pinecone index settings, and Azure VM specifications still need to be finalized during implementation.
 
## Success Criteria
 
The MVP will be considered successful when:
 
1. Hieu's mock PDFs can be processed and indexed without errors.
2. The chatbot retrieves the exact relevant information for questions whose answers are present in those PDFs.
3. Generated answers accurately reflect the retrieved passages and display the supporting document source.
4. Questions not supported by the PDFs receive a clear not-found response rather than a fabricated answer.
5. In-session follow-up questions retain the necessary conversation context.
6. A reviewer can complete the password-protected workflow through the Azure VM public IP without application errors.
 
No numerical accuracy or latency threshold is defined yet. A representative evaluation question set will be created from the supplied PDFs when they become available.
 
## Risks & Assumptions
 
| Risk or Assumption | Mitigation |
|---|---|
| Mock documents are delayed or do not cover enough scenarios. | Request the PDFs early and create the evaluation questions immediately after receiving them. |
| The model may generate unsupported information. | Use a strict grounding prompt, require retrieved context, set a relevance threshold, and return a not-found response when evidence is insufficient. |
| Poor chunking or retrieval settings may return incomplete passages. | Test chunk size, overlap, retrieval count, metadata, and representative questions against the supplied PDFs. |
| The Azure VM public IP exposes a test application. | Require a Streamlit password, keep secrets in environment variables, restrict network access where possible, and close public access after the demo. |
| OpenAI or Pinecone may be unavailable or incur unexpected cost. | Add error handling, monitor usage, limit test data and requests, and document required service configuration. |
| Internal documents may contain confidential information. | Use only authorized mock data for the demo, avoid logging sensitive content, and do not commit documents or credentials to source control. |
| Exact model and infrastructure settings are not finalized. | Keep these settings environment-driven and validate compatible choices before deployment. |
| The supplied PDFs are assumed to be authorized mock company documents. | Confirm document authorization before ingestion and restrict the demo to the approved files. |
 
## Demo Scenario
 
1. The reviewer opens the Streamlit application using the Azure VM public IP.
2. The reviewer enters the Streamlit demo password.
3. The application confirms that Hieu's mock PDFs have been indexed.
4. The reviewer asks a question whose answer appears in one of the PDFs.
5. The chatbot retrieves the relevant passage, gives an accurate answer, and displays the source document.
6. The reviewer asks a follow-up question to verify in-session chat memory.
7. The reviewer compares the answer with the cited PDF content.
8. The reviewer asks a question not covered by any indexed PDF.
9. The chatbot clearly states that the information could not be found and does not invent an answer.
 
## Delivery
 
- Submit the completed proposal by email to **HieuNT14** and **AnhNM66** for review and scoring.
- Push the project to the team GitLab repository when it becomes available.

## Thought:

RAG retrieval can be improve by passing result to a summarization pipeline in transformer? (save token) and then pass the summary to question-answering task model?


## future code structure

```
chat_bot_rag/
│
├── .env                           # Environment variables (OpenAI, Pinecone keys, passwords)
├── .gitignore                     # Ignores .env, virtual environments, data/ PDFs, cache
├── README.md                      # Setup instructions (migrated from readme.txt)
├── requirements.txt               # Dependencies (streamlit, langchain, pinecone, pypdf)
│
├── data/                          # Folder for PDFs (add data/ to .gitignore!)
│   └── mock_pdfs/                 # Where Hieu's mock PDFs will live locally
│
├── src/                           # Main code folder
│   ├── __init__.py
│   ├── config.py                  # Loads & validates env vars (e.g., passwords, keys)
│   │
│   ├── ingest/                    # Data ingestion pipeline (Admin use)
│   │   ├── __init__.py
│   │   ├── parsing.py             # PDF parsing & text extraction (from your functions/)
│   │   ├── chunking.py            # Handles LangChain splitters (recursive, semantic)
│   │   └── indexing.py            # Generates embeddings and uploads to Pinecone
│   │
│   ├── rag/                       # RAG Pipeline (Query -> Retrieval -> Response)
│   │   ├── __init__.py
│   │   ├── retriever.py           # Connects to Pinecone, runs query, does reranking
│   │   ├── generator.py           # Formats grounding prompt and queries OpenAI Chat Model
│   │   └── history.py             # In-session memory formatting helper
│   │
│   └── ui/                        # Frontend components (Streamlit specific)
│       ├── __init__.py
│       ├── auth.py                # Password protection system
│       └── components.py          # Chat bubbles, sidebar controls, source citations
│
├── tests/                         # Unit tests for extraction & retrieval quality
│   └── ...
│
└── app.py                         # Main entrypoint run by Streamlit ("streamlit run app.py")

```