"""Stage 3 — LangChain retriever with score threshold + dedup.

Works with any vector store backend (Pinecone or ChromaDB).
"""

from __future__ import annotations

from dataclasses import replace

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict

from src.config import Settings
from src.lc.documents import document_to_search_result
from src.lc.embeddings import build_embeddings
from src.lc.vectorstore import LangChainVectorStoreAdapter
from src.models import SearchResult


class LangChainRetriever(BaseRetriever):
    """LC BaseRetriever with score threshold and optional embedding dedup."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    vectorstore: LangChainVectorStoreAdapter
    settings: Settings
    top_k: int | None = None
    score_threshold: float | None = None
    content_type: str | None = None
    deduplicate: bool | None = None
    dedup_threshold: float | None = None

    def _get_relevant_documents(self, query: str) -> list[Document]:
        results = self._search_results(query)
        docs: list[Document] = []
        for item in results:
            docs.append(
                Document(
                    page_content=item.text,
                    metadata={
                        "source_file": item.source_file,
                        "page": item.page,
                        "content_type": item.content_type,
                        "heading": item.heading,
                        "image_path": item.image_path,
                        "ahash": item.ahash,
                        "score": item.score,
                    },
                )
            )
        return docs

    def _search_results(self, query: str) -> list[SearchResult]:
        if not query.strip():
            return []

        selected_top_k = self.top_k or self.settings.retrieval_top_k
        use_dedup = (
            self.settings.retrieval_dedup_enabled
            if self.deduplicate is None
            else self.deduplicate
        )
        selected_dedup_threshold = (
            self.settings.retrieval_dedup_threshold
            if self.dedup_threshold is None
            else self.dedup_threshold
        )
        fetch_k = (
            selected_top_k * self.settings.retrieval_candidate_multiplier
            if use_dedup
            else selected_top_k
        )
        metadata_filter = None
        if self.content_type:
            metadata_filter = {"content_type": {"$eq": self.content_type}}

        paired = self.vectorstore.similarity_search_with_score(
            query,
            k=fetch_k,
            score_threshold=(
                self.settings.retrieval_score_threshold
                if self.score_threshold is None
                else self.score_threshold
            ),
            metadata_filter=metadata_filter,
            include_values=use_dedup,
        )

        candidates: list[SearchResult] = []
        for doc, score in paired:
            vector = doc.metadata.pop("_vector", None)
            candidates.append(
                document_to_search_result(doc, score=score, vector=vector)
            )

        if not use_dedup:
            return [replace(item, vector=None) for item in candidates[:selected_top_k]]

        # Lazy import avoids circular dependency with src.rag.retriever.
        from src.rag.retriever import deduplicate_results

        return deduplicate_results(
            candidates,
            top_k=selected_top_k,
            dedup_threshold=selected_dedup_threshold,
        )


class LangChainSemanticRetriever:
    """Semantic search facade over LangChain embeddings + vector store backend."""

    def __init__(self, settings: Settings):
        settings.validate_for_vector_store()
        self.settings = settings
        self.embeddings = build_embeddings(settings)
        self.vectorstore = LangChainVectorStoreAdapter(
            settings,
            self.embeddings,
            create_if_missing=True,
        )
        self.store = self.vectorstore.store

    def search(
        self,
        query: str,
        top_k: int | None = None,
        score_threshold: float | None = None,
        content_type: str | None = None,
        deduplicate: bool | None = None,
        dedup_threshold: float | None = None,
    ) -> list[SearchResult]:
        """Retrieve top chunks for a text query (threshold + optional dedup)."""
        retriever = LangChainRetriever(
            vectorstore=self.vectorstore,
            settings=self.settings,
            top_k=top_k,
            score_threshold=score_threshold,
            content_type=content_type,
            deduplicate=deduplicate,
            dedup_threshold=dedup_threshold,
        )
        return retriever._search_results(query)

    def search_image_by_hash(
        self,
        image_path_or_hash: str,
        max_distance: int = 5,
    ) -> list[SearchResult]:
        """Find visual chunks by average-hash distance."""
        return self.vectorstore.search_by_ahash(
            image_path_or_hash,
            max_distance=max_distance,
        )
