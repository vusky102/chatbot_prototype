"""Stage 4 — LCEL answer chain (prompt | llm | parser)."""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from src.config import Settings
from src.models import SearchResult


SYSTEM_PROMPT = """
You are an advanced Internal Knowledge Assistant executing a precise Retrieval-Augmented Generation (RAG) pipeline. 

# YOUR CORE JOB
Your sole responsibility is to answer user queries by synthesizing and analyzing ONLY the provided "Retrieved context chunks". These chunks may contain dense text, mathematical formulas, or descriptions of visual data (like graphs or diagrams) extracted from internal documents.

# OUTPUT RULES & CITATIONS
1. **Grounding:** Every single claim, fact, or explanation you provide MUST be directly supported by the context. 
2. **Citations:** You must aggressively cite your sources inline. Whenever you state a fact derived from a chunk, append the citation in brackets immediately after the statement using the exact source file and page provided in the chunk metadata (e.g., `[Public_035.pdf, page 6]`).
3. **Synthesis:** If multiple chunks contain related information, intelligently combine them into a cohesive, highly analytical, and easy-to-read response.
4. **Language:** You must always respond in the exact same language as the user's question, regardless of the language of the source documents.

# HALLUCINATION BOUNDARIES
- **NEVER** guess, invent, or use outside knowledge to answer the specific details of the prompt.
- If the provided context simply does not contain enough evidence to formulate a complete answer, you must clearly and explicitly state that the information is missing from the knowledge base (translating this admission into the user's chosen language). Do not attempt to fill in the blanks.
""".strip()


def build_chat_model(settings: Settings) -> Runnable:
    """Construct the chat LLM used by the grounded answer chain."""
    model_lower = settings.chat_model.lower()
    
    if model_lower.startswith("gemini"):
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.chat_model,
            google_api_key=settings.gemini_api_key,
            temperature=0.0
        )
    elif "/" in settings.chat_model:
        # Route to OpenRouter for models with paths (e.g. meta-llama/...)
        kwargs: dict[str, object] = {
            "model": settings.chat_model,
            "api_key": settings.openrouter_api_key,
            "temperature": 0.0,
        }
        if settings.openrouter_base_url:
            kwargs["base_url"] = settings.openrouter_base_url
        return ChatOpenAI(**kwargs)
    else:
        # Standard OpenAI route
        kwargs: dict[str, object] = {
            "model": settings.chat_model,
            "api_key": settings.openai_api_key,
            "temperature": 0.0,
        }
        if settings.openai_base_url:
            kwargs["base_url"] = settings.openai_base_url
        return ChatOpenAI(**kwargs)


def build_answer_chain(settings: Settings) -> Runnable:
    """Return LCEL chain: dict(question, context[, history]) → answer string."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("placeholder", "{history}"),
            (
                "human",
                "Question:\n{question}\n\nRetrieved context:\n{context}",
            ),
        ]
    )
    llm = build_chat_model(settings)
    return prompt | llm | StrOutputParser()


class LangChainGroundedGenerator:
    """Workshop generator implemented with LangChain LCEL."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.chain = build_answer_chain(settings)

    def generate(
        self,
        question: str,
        results: list[SearchResult],
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Generate an answer grounded in `results`, optionally with chat history."""
        if not results:
            return "Không tìm thấy thông tin phù hợp trong kho tài liệu."

        from src.rag.retriever import format_context

        history_messages: list[tuple[str, str]] = []
        if history:
            for item in history[-6:]:
                role = item.get("role", "user")
                content = item.get("content", "")
                if role == "assistant":
                    history_messages.append(("ai", content))
                else:
                    history_messages.append(("human", content))

        context_str = format_context(results)
        
        print("\n\n" + "="*50)
        print("=== FINAL DATA FED TO AI ===")
        print("="*50)
        print(f"QUESTION (Including any extracted visual caption):\n{question}\n")
        print(f"RETRIEVED CONTEXT CHUNKS:\n{context_str}")
        print("="*50 + "\n\n")

        return self.chain.invoke(
            {
                "question": question,
                "context": context_str,
                "history": history_messages,
            }
        )
