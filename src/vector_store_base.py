"""Abstract base class for vector store backends (Pinecone / ChromaDB)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from src.config import Settings
from src.models import DocumentChunk, SearchResult


class VectorStoreBackend(ABC):
    """Unified interface for vector store operations.

    Concrete subclasses:
        - ``PineconeVectorStore``  (cloud, hybrid BM25+dense)
        - ``ChromaDBVectorStore``  (local, dense-only)
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Return ``"pinecone"`` or ``"chromadb"``."""

    @abstractmethod
    def connect(self, create_if_missing: bool = False) -> "VectorStoreBackend":
        """Open / create the underlying index / collection."""

    @abstractmethod
    def upsert(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        batch_size: int = 100,
    ) -> int:
        """Insert or update vectors; return the number of records written."""

    @abstractmethod
    def search(
        self,
        query_vector: list[float],
        top_k: int,
        score_threshold: float,
        metadata_filter: dict | None = None,
        include_values: bool = False,
        query_text: str = "",
        alpha: float = 0.5,
    ) -> list[SearchResult]:
        """Semantic search; return results above *score_threshold*."""

    @abstractmethod
    def search_by_ahash(
        self,
        image_path_or_hash: str,
        max_distance: int = 5,
    ) -> list[SearchResult]:
        """Find visuals whose aHash is within Hamming distance of the query."""

    @abstractmethod
    def delete_source(self, source_file: str) -> int:
        """Delete all vectors for *source_file*; return deleted count."""

    @abstractmethod
    def get_stats(self) -> dict[str, object]:
        """Return index/collection statistics."""
