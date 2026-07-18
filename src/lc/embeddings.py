"""Stage 2 — LangChain OpenAI embeddings."""

from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from src.config import Settings


def build_embeddings(settings: Settings) -> OpenAIEmbeddings:
    """Build LangChain OpenAI embeddings from workshop settings."""
    kwargs: dict[str, object] = {
        "model": settings.embedding_model,
        "api_key": settings.embedding_api_key,
    }
    if settings.embedding_base_url:
        kwargs["base_url"] = settings.embedding_base_url
    if settings.embedding_model.startswith("text-embedding-3"):
        kwargs["dimensions"] = settings.embedding_dimension
    return OpenAIEmbeddings(**kwargs)
