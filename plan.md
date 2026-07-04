Internal Company Assistant using RAG and Streamlit

## Reason for Choosing the Topic

Employees often spend time searching for company documents or repeatedly asking HR and IT about policies, onboarding, and technical issues. This project provides an AI assistant that delivers instant answers using the company’s internal knowledge base, improving efficiency and reducing support workload.

⸻

## Pain Points

* Company knowledge is scattered across multiple documents.
* HR and IT receive many repetitive questions.
* Traditional keyword search is slow and often ineffective.

Input Sources

* PDF
* DOCX
* TXT
* Employee handbook
* IT manuals
* FAQ documents

⸻

## Proposed Solution

Build an AI assistant using RAG and Streamlit that:

1. Indexes company documents into a vector database.
2. Retrieves relevant information based on employee questions.
3. Uses an LLM to generate accurate, context-aware answers.
4. Displays the answer with its document source.

⸻

## Benefits

* Faster information retrieval.
* Reduced HR and IT workload.
* Consistent answers from official documents.
* Improved employee productivity and onboarding experience.

⸻

## Flow:

Company Docs
   ↓
Chunking + Embedding
   ↓
Vector DB
   ↓
User asks question in Streamlit
   ↓
RAG retrieves relevant company knowledge
   ↓
LLM generates answer
   ↓
Streamlit shows answer + source

⸻

## Stack:

Frontend: Streamlit
Backend: Python
RAG: LangChain
Vector DB: Pinecone
Embedding: OpenAI / local embedding model
LLM: GPT 
Data: PDF, DOCX, QSM


