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
provided context. If the context does not contain enough evidence, say that the
information was not found in the knowledge base. Never invent details.

Use the same language as the question. Add inline citations in the exact format
[source_file, page N] after supported statements. Keep the answer concise.
""".strip()


def build_chat_model(settings: Settings) -> ChatOpenAI:
    """Construct the chat LLM used by the grounded answer chain."""
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
