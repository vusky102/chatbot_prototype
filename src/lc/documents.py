"""Convert between workshop models and LangChain Documents."""

from __future__ import annotations

from langchain_core.documents import Document

from src.models import DocumentChunk, SearchResult


def chunk_to_document(chunk: DocumentChunk) -> Document:
    """Convert a workshop `DocumentChunk` into a LangChain `Document`."""
    metadata = chunk.metadata()
    metadata["id"] = chunk.id
    return Document(page_content=chunk.text, metadata=metadata)


def document_to_chunk(doc: Document, chunk_index: int = 0) -> DocumentChunk:
    """Convert a LangChain `Document` back into a workshop `DocumentChunk`."""
    meta = dict(doc.metadata or {})
    return DocumentChunk(
        id=str(meta.get("id") or f"lc-{chunk_index}"),
        text=doc.page_content,
        source_file=str(meta.get("source_file", "unknown")),
        page=int(meta.get("page", 0) or 0),
        content_type=str(meta.get("content_type", "text")),
        heading=str(meta.get("heading", "")),
        image_path=str(meta.get("image_path", "")),
        ahash=str(meta.get("ahash", "")),
        chunk_index=int(meta.get("chunk_index", chunk_index) or chunk_index),
    )


def document_to_search_result(
    doc: Document,
    score: float,
    vector: list[float] | None = None,
) -> SearchResult:
    """Convert a retrieved LangChain `Document` into a workshop `SearchResult`."""
    meta = dict(doc.metadata or {})
    return SearchResult(
        text=doc.page_content,
        score=float(score),
        source_file=str(meta.get("source_file", "unknown")),
        page=int(meta.get("page", 0) or 0),
        content_type=str(meta.get("content_type", "text")),
        heading=str(meta.get("heading", "")),
        image_path=str(meta.get("image_path", "")),
        ahash=str(meta.get("ahash", "")),
        raw_metadata=meta,
        vector=vector,
    )
