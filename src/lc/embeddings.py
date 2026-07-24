"""Stage 2 — LangChain OpenAI embeddings."""

from __future__ import annotations

from langchain_openai import OpenAIEmbeddings

from src.config import Settings


import tiktoken
from src.utils.token_tracker import TokenTracker

class TrackedEmbeddings(OpenAIEmbeddings):
    
    def _track(self, texts: list[str]) -> None:
        try:
            try:
                encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                encoding = tiktoken.get_encoding("cl100k_base")
                
            tokens = sum(len(encoding.encode(text)) for text in texts)
            if tokens > 0:
                tracker = TokenTracker()
                tracker.record(
                    model=self.model,
                    provider="OpenAI",
                    operation="embedding",
                    input_tokens=tokens,
                    output_tokens=0
                )
        except Exception as e:
            print(f"Warning: Failed to track embedding tokens: {e}")

    def embed_documents(self, texts: list[str], chunk_size: int | None = 0) -> list[list[float]]:
        self._track(texts)
        return super().embed_documents(texts, chunk_size=chunk_size)

    def embed_query(self, text: str) -> list[float]:
        self._track([text])
        return super().embed_query(text)

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
    return TrackedEmbeddings(**kwargs)
