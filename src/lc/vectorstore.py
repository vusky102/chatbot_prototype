"""Stage 2 — LangChain VectorStore adapter over the Pinecone SDK client.

Python 3.14 cannot install langchain-pinecone yet, so we implement the
LangChain VectorStore interface on top of our existing Pinecone SDK store.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import VectorStore

from src.config import Settings
from src.lc.documents import chunk_to_document
from src.models import DocumentChunk
from src.vector_store import PineconeVectorStore


class LangChainPineconeVectorStore(VectorStore):
    """LangChain-compatible vector store backed by `PineconeVectorStore`."""

    def __init__(
        self,
        settings: Settings,
        embedding: Embeddings,
        *,
        create_if_missing: bool = False,
        store: PineconeVectorStore | None = None,
    ):
        self._settings = settings
        self._embedding = embedding
        self._store = store or PineconeVectorStore(settings).connect(
            create_if_missing=create_if_missing
        )

    @property
    def embeddings(self) -> Embeddings:
        """LangChain embeddings client used by this store."""
        return self._embedding

    @property
    def store(self) -> PineconeVectorStore:
        """Underlying Pinecone SDK wrapper (`src.vector_store`)."""
        return self._store

    @classmethod
    def from_texts(
        cls,
        texts: list[str],
        embedding: Embeddings,
        metadatas: list[dict] | None = None,
        *,
        settings: Settings | None = None,
        **kwargs: Any,
    ) -> "LangChainPineconeVectorStore":
        """Create a store and index the provided texts (LangChain API)."""
        if settings is None:
            raise ValueError("settings is required")
        instance = cls(settings, embedding, create_if_missing=True)
        instance.add_texts(texts, metadatas=metadatas, **kwargs)
        return instance

    def add_texts(
        self,
        texts: Iterable[str],
        metadatas: list[dict] | None = None,
        *,
        ids: list[str] | None = None,
        **kwargs: Any,
    ) -> list[str]:
        """Embed and upsert texts; return assigned vector ids."""
        text_list = list(texts)
        meta_list = metadatas or [{} for _ in text_list]
        if len(meta_list) != len(text_list):
            raise ValueError("metadatas length must match texts")

        chunks: list[DocumentChunk] = []
        for index, (text, meta) in enumerate(zip(text_list, meta_list)):
            chunk_id = (ids[index] if ids else None) or str(meta.get("id") or f"lc-{index}")
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    text=text,
                    source_file=str(meta.get("source_file", "unknown")),
                    page=int(meta.get("page", 0) or 0),
                    content_type=str(meta.get("content_type", "text")),
                    heading=str(meta.get("heading", "")),
                    image_path=str(meta.get("image_path", "")),
                    ahash=str(meta.get("ahash", "")),
                    chunk_index=int(meta.get("chunk_index", index) or index),
                )
            )

        vectors = self._embedding.embed_documents([chunk.text for chunk in chunks])
        self._store.upsert(chunks, vectors)
        return [chunk.id for chunk in chunks]

    def add_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Embed workshop chunks and upsert them; return upserted count."""
        if not chunks:
            return 0
        vectors = self._embedding.embed_documents([chunk.text for chunk in chunks])
        return self._store.upsert(chunks, vectors)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        **kwargs: Any,
    ) -> list[Document]:
        """Return the top-k LangChain documents for a query."""
        docs_and_scores = self.similarity_search_with_score(query, k=k, **kwargs)
        return [doc for doc, _score in docs_and_scores]

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        *,
        score_threshold: float = 0.0,
        metadata_filter: dict | None = None,
        include_values: bool = False,
        **kwargs: Any,
    ) -> list[tuple[Document, float]]:
        """Return (document, score) pairs above an optional score threshold."""
        query_vector = self._embedding.embed_query(query)
        results = self._store.search(
            query_vector=query_vector,
            top_k=k,
            score_threshold=score_threshold,
            metadata_filter=metadata_filter,
            include_values=include_values,
        )
        paired: list[tuple[Document, float]] = []
        for item in results:
            chunk = DocumentChunk(
                id=str(item.raw_metadata.get("id", "")),
                text=item.text,
                source_file=item.source_file,
                page=item.page,
                content_type=item.content_type,
                heading=item.heading,
                image_path=item.image_path,
                ahash=item.ahash,
            )
            doc = chunk_to_document(chunk)
            if item.vector is not None:
                doc.metadata["_vector"] = item.vector
            paired.append((doc, float(item.score)))
        return paired

    def delete(self, ids: list[str] | None = None, **kwargs: Any) -> None | bool:
        """Delete by `source_file` kwarg when provided (ids path is limited)."""
        source_file = kwargs.get("source_file")
        if source_file:
            self._store.delete_source(str(source_file))
            return True
        if not ids:
            return False
        # Best-effort: delete by source when ids unavailable in filter path.
        return False

    def delete_source(self, source_file: str) -> int:
        """Delete all vectors for a source file name."""
        return self._store.delete_source(source_file)

    def get_stats(self) -> dict[str, object]:
        """Return Pinecone index statistics for this namespace."""
        return self._store.get_stats()

    def search_by_ahash(self, image_path_or_hash: str, max_distance: int = 5):
        """Find visual chunks by average-hash distance."""
        return self._store.search_by_ahash(
            image_path_or_hash,
            max_distance=max_distance,
        )
