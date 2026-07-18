"""LangChain RAG retrieval tool shared by the CLI chatbot."""

from __future__ import annotations

from langchain_core.tools import tool

_rag_service = None


def _get_rag_service():
    """Lazy-init shared RAGService for tool calls."""
    global _rag_service
    if _rag_service is None:
        from src.rag import RAGService

        _rag_service = RAGService()
    return _rag_service


@tool
def retrieve_knowledge(query: str) -> str:
    """Semantically search approved internal PDF documents.

    Returns relevant text, table, chart, diagram and image descriptions
    with source citations.

    Args:
        query: Search query based on the employee's question.
    """
    return _get_rag_service().retrieve_as_text(query)


RAG_TOOLS = [retrieve_knowledge]
RAG_TOOL_MAP = {tool_fn.name: tool_fn for tool_fn in RAG_TOOLS}
