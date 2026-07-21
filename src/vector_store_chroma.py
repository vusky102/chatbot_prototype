"""ChromaDB vector store backend — local, dense-only semantic search."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import chromadb

from src.config import Settings
from src.ingest.ahash import compute_ahash, hamming_distance
from src.models import DocumentChunk, SearchResult
from src.vector_store_base import VectorStoreBackend

# aHash is 64 bits; used to turn Hamming distance into a [0, 1] similarity score.
_AHASH_BITS = 64

# Hardcoded defaults (no .env needed).
_DEFAULT_PERSIST_DIR = "./chroma_db"
_DEFAULT_COLLECTION_NAME = "rag-chatbot"


def _metadata_to_search_result(
    metadata: dict,
    score: float,
    vector: list[float] | None = None,
) -> SearchResult:
    return SearchResult(
        text=str(metadata.get("text", "")),
        score=score,
        source_file=str(metadata.get("source_file", "unknown")),
        page=int(metadata.get("page", 0)),
        content_type=str(metadata.get("content_type", "text")),
        heading=str(metadata.get("heading", "")),
        image_path=str(metadata.get("image_path", "")),
        ahash=str(metadata.get("ahash", "")),
        raw_metadata=metadata,
        vector=vector,
    )


def _batches(items: list, size: int) -> Iterable[list]:
    for start in range(0, len(items), size):
        yield items[start : start + size]


class ChromaDBVectorStore(VectorStoreBackend):
    """Local ChromaDB backend with persistent storage and cosine distance.

    Provides dense-only semantic search (no BM25/hybrid). The ``query_text``
    and ``alpha`` parameters on ``search()`` are accepted but ignored.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._collection = None
        self._client = None

    # -- public interface ---------------------------------------------------

    @property
    def backend_name(self) -> str:
        return "chromadb"

    def connect(self, create_if_missing: bool = False) -> "ChromaDBVectorStore":
        persist_path = Path(_DEFAULT_PERSIST_DIR).resolve()
        persist_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(persist_path))
        self._collection = self._client.get_or_create_collection(
            name=_DEFAULT_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return self

    def upsert(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        batch_size: int = 100,
    ) -> int:
        self._require_collection()
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")

        total = 0
        for batch_chunks, batch_vectors in zip(
            _batches(chunks, batch_size),
            _batches(vectors, batch_size),
        ):
            ids = [chunk.id for chunk in batch_chunks]
            documents = [chunk.text for chunk in batch_chunks]
            metadatas = [chunk.metadata() for chunk in batch_chunks]
            embeddings = list(batch_vectors)

            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            total += len(ids)

        return total

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        score_threshold: float,
        metadata_filter: dict | None = None,
        include_values: bool = False,
        query_text: str = "",  # ignored — no BM25 in ChromaDB
        alpha: float = 0.5,   # ignored — dense only
    ) -> list[SearchResult]:
        self._require_collection()

        kwargs: dict = {
            "query_embeddings": [query_vector],
            "n_results": min(top_k, max(self._collection.count(), 1)),
            "include": ["documents", "distances", "metadatas"],
        }
        if include_values:
            kwargs["include"].append("embeddings")
        if metadata_filter:
            kwargs["where"] = self._translate_filter(metadata_filter)

        response = self._collection.query(**kwargs)

        if (
            not response
            or not response.get("documents")
            or not response["documents"][0]
        ):
            return []

        results: list[SearchResult] = []
        seen_ids: set[str] = set()
        ids_list = response.get("ids", [[]])[0]
        docs_list = response["documents"][0]
        dist_list = (response.get("distances") or [[]])[0]
        meta_list = (response.get("metadatas") or [[]])[0]
        emb_list = (response.get("embeddings") or [[]])[0] if include_values else [None] * len(docs_list)

        for i, doc_text in enumerate(docs_list):
            doc_id = ids_list[i] if i < len(ids_list) else ""
            if doc_id in seen_ids:
                continue
            seen_ids.add(doc_id)

            # ChromaDB cosine distance ∈ [0, 2]; convert to similarity score.
            distance = dist_list[i] if i < len(dist_list) else 1.0
            score = max(0.0, 1.0 - distance)

            if score < score_threshold:
                continue

            metadata = dict(meta_list[i]) if i < len(meta_list) else {}
            if "text" not in metadata:
                metadata["text"] = doc_text

            emb = emb_list[i] if i < len(emb_list) else None
            results.append(
                _metadata_to_search_result(
                    metadata,
                    score=score,
                    vector=list(emb) if include_values and emb else None,
                )
            )

        return results

    def search_by_ahash(
        self,
        image_path_or_hash: str,
        max_distance: int = 5,
    ) -> list[SearchResult]:
        self._require_collection()
        path = Path(image_path_or_hash)
        if path.is_file():
            query_hash = compute_ahash(path)
        else:
            query_hash = image_path_or_hash.strip()
        if not query_hash:
            return []

        count = self._collection.count()
        if count == 0:
            return []

        all_records = self._collection.get(
            include=["metadatas"],
            limit=count,
        )

        matches: list[SearchResult] = []
        for metadata in all_records.get("metadatas") or []:
            stored_hash = str(metadata.get("ahash", ""))
            if not stored_hash:
                continue
            distance = hamming_distance(query_hash, stored_hash)
            if distance > max_distance:
                continue
            similarity = max(0.0, 1.0 - (distance / _AHASH_BITS))
            enriched = {
                **metadata,
                "hamming_distance": distance,
                "query_ahash": query_hash,
            }
            matches.append(_metadata_to_search_result(enriched, score=similarity))

        matches.sort(
            key=lambda item: int(item.raw_metadata.get("hamming_distance", _AHASH_BITS))
        )
        return matches

    def delete_source(self, source_file: str) -> int:
        self._require_collection()
        target = source_file.strip()
        if not target:
            return 0

        try:
            existing = self._collection.get(
                where={"source_file": target},
                include=[],
            )
        except Exception:
            return 0

        ids_to_delete = existing.get("ids") or []
        if not ids_to_delete:
            return 0

        # ChromaDB delete accepts up to ~5000 ids at once; batch for safety.
        for batch in _batches(ids_to_delete, 1000):
            self._collection.delete(ids=batch)

        return len(ids_to_delete)

    def get_stats(self) -> dict[str, object]:
        self._require_collection()
        count = self._collection.count()

        source_files: set[str] = set()
        text_chunks = 0
        visual_chunks = 0

        if count > 0:
            all_records = self._collection.get(
                include=["metadatas"],
                limit=count,
            )
            for metadata in all_records.get("metadatas") or []:
                source_files.add(str(metadata.get("source_file", "unknown")))
                if metadata.get("image_path") or metadata.get("ahash"):
                    visual_chunks += 1
                else:
                    text_chunks += 1

        return {
            "namespace": _DEFAULT_COLLECTION_NAME,
            "index_name": "chromadb-local",
            "vector_count": count,
            "text_chunks": text_chunks,
            "visual_chunks": visual_chunks,
            "source_files": sorted(source_files),
        }

    # -- private helpers ----------------------------------------------------

    def _require_collection(self) -> None:
        if self._collection is None:
            raise RuntimeError("Call connect() before using the vector store")

    @staticmethod
    def _translate_filter(pinecone_filter: dict) -> dict:
        """Translate Pinecone-style metadata filter to ChromaDB ``where`` syntax.

        Pinecone:  ``{"field": {"$eq": val}}``
        ChromaDB:  ``{"field": {"$eq": val}}``  (same for $eq, $ne, $gt, etc.)

        Simple case ``{"field": val}`` is also accepted by ChromaDB.
        """
        # The filter syntax is largely compatible; pass through as-is.
        return pinecone_filter
