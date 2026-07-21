"""Factory for creating the appropriate vector store backend.

Default behaviour:
    1. If user selected ``"pinecone"`` → use Pinecone.
    2. If user selected ``"chromadb"`` → use ChromaDB.
    3. On startup (no explicit choice), try Pinecone first;
       if the API key is missing or connection fails, fall back to ChromaDB.
"""

from __future__ import annotations

from src.config import Settings
from src.vector_store_base import VectorStoreBackend


def create_vector_store(settings: Settings, backend: str = "auto") -> VectorStoreBackend:
    """Instantiate and connect the requested vector store backend.

    Args:
        settings: Application settings.
        backend: ``"pinecone"``, ``"chromadb"``, or ``"auto"`` (try Pinecone,
                 fall back to ChromaDB).

    Returns:
        A connected ``VectorStoreBackend`` instance.
    """
    backend = backend.strip().lower()

    if backend == "chromadb":
        return _make_chroma(settings)

    if backend == "pinecone":
        return _make_pinecone(settings)

    # "auto" — try Pinecone, gracefully fall back to ChromaDB.
    if settings.pinecone_api_key:
        try:
            return _make_pinecone(settings)
        except Exception as exc:
            print(
                f"[VectorStore] Pinecone connection failed ({exc}); "
                "falling back to ChromaDB."
            )

    return _make_chroma(settings)


def _make_pinecone(settings: Settings) -> VectorStoreBackend:
    from src.vector_store import PineconeVectorStore

    store = PineconeVectorStore(settings)
    store.connect(create_if_missing=True)
    return store


def _make_chroma(settings: Settings) -> VectorStoreBackend:
    from src.vector_store_chroma import ChromaDBVectorStore

    store = ChromaDBVectorStore(settings)
    store.connect(create_if_missing=True)
    return store
