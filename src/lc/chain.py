"""Stage 4 — LCEL answer chain (prompt | llm | parser)."""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from src.config import Settings
from src.models import SearchResult


SYSTEM_PROMPT = """
You are an internal document assistant. Answer only with facts supported by the
provided context. If the context does not contain enough evidence, clearly state that the information is not available in the knowledge base (translate this statement to the user's language). Never invent details.

Use the same language as the question. Add inline citations containing the source file name and page number in brackets (e.g., [document.pdf, page 6]) after supported statements. Keep the answer concise.
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

        return self.chain.invoke(
            {
                "question": question,
                "context": format_context(results),
                "history": history_messages,
            }
        )
