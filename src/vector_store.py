import time
from collections.abc import Iterable
from pathlib import Path

from pinecone import Pinecone, ServerlessSpec
from pinecone_text.sparse import BM25Encoder
from pinecone_text.hybrid import hybrid_convex_scale

try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
except Exception:
    pass

from src.config import Settings
from src.ingest.ahash import compute_ahash, hamming_distance
from src.models import DocumentChunk, SearchResult
from src.vector_store_base import VectorStoreBackend


# aHash is 64 bits; used to turn Hamming distance into a [0, 1] similarity score.
_AHASH_BITS = 64


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


class PineconeVectorStore(VectorStoreBackend):
    @property
    def backend_name(self) -> str:
        return "pinecone"

    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.client = Pinecone(api_key=settings.pinecone_api_key, pool_threads=30)
        self.index = None
        self.bm25 = BM25Encoder().default()

    def connect(self, create_if_missing: bool = False):
        names = set(self.client.list_indexes().names())
        if self.settings.pinecone_index_name not in names:
            if not create_if_missing:
                raise RuntimeError(
                    f"Pinecone index '{self.settings.pinecone_index_name}' does not exist"
                )
            self.client.create_index(
                name=self.settings.pinecone_index_name,
                dimension=self.settings.embedding_dimension,
                metric="dotproduct",
                spec=ServerlessSpec(
                    cloud=self.settings.pinecone_cloud,
                    region=self.settings.pinecone_region,
                ),
            )
            self._wait_until_ready()
        else:
            description = self.client.describe_index(
                self.settings.pinecone_index_name
            )
            dimension = getattr(description, "dimension", None)
            if (
                dimension is not None
                and dimension != self.settings.embedding_dimension
            ):
                raise RuntimeError(
                    f"Pinecone index dimension is {dimension}, but "
                    f"OPENAI_EMBEDDING_DIMENSION is "
                    f"{self.settings.embedding_dimension}"
                )
        self.index = self.client.Index(
            self.settings.pinecone_index_name,
            pool_threads=30
        )
        return self

    def _wait_until_ready(self, timeout_seconds: int = 120) -> None:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            description = self.client.describe_index(
                self.settings.pinecone_index_name
            )
            status = getattr(description, "status", {})
            ready = getattr(status, "ready", None)
            if ready is None and isinstance(status, dict):
                ready = status.get("ready")
            if ready:
                return
            time.sleep(2)
        raise TimeoutError("Timed out waiting for Pinecone index to become ready")

    def delete_source(self, source_file: str) -> int:
        """
        Delete all vectors whose metadata source_file matches.

        Prefers delete-by-id (works on all Pinecone indexes). Falls back to
        metadata filter delete if listing finds nothing but namespace exists.
        Returns the number of vector IDs requested for deletion.
        """
        self._require_index()
        target = source_file.strip()
        if not target:
            return 0

        ids_to_delete = [
            vector_id
            for vector_id, metadata in self._iter_records()
            if str(metadata.get("source_file", "")) == target
        ]

        deleted = 0
        if ids_to_delete:
            for batch in _batches(
                [{"id": vector_id} for vector_id in ids_to_delete],
                1000,
            ):
                self.index.delete(
                    ids=[item["id"] for item in batch],
                    namespace=self.settings.pinecone_namespace,
                )
            return len(ids_to_delete)

        # Fallback: metadata filter (supported on newer serverless indexes).
        try:
            self.index.delete(
                namespace=self.settings.pinecone_namespace,
                filter={"source_file": {"$eq": target}},
            )
        except Exception as exc:
            # If the namespace/index doesn't exist or is empty, there is nothing to delete.
            exc_str = str(exc).lower()
            if "namespace not found" in exc_str or getattr(exc, "status", None) == 404:
                return 0
            # Older serverless indexes may reject filter deletes.
            raise RuntimeError(
                f"No vectors found for source_file={target!r}, and "
                "metadata-filter delete is not supported on this index."
            ) from None
        return 0

    def upsert(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
        batch_size: int = 100,
    ) -> int:
        self._require_index()
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors must have the same length")

        texts = [chunk.text for chunk in chunks]
        sparse_vectors = self.bm25.encode_documents(texts)

        records = [
            {
                "id": chunk.id, 
                "values": vector, 
                "sparse_values": sparse, 
                "metadata": chunk.metadata()
            }
            for chunk, vector, sparse in zip(chunks, vectors, sparse_vectors)
        ]
        for batch in _batches(records, batch_size):
            try:
                self.index.upsert(
                    vectors=batch,
                    namespace=self.settings.pinecone_namespace,
                )
            except Exception as e:
                import logging
                from src.utils.logger import get_logger
                logger = get_logger("pinecone_upsert")
                logger.error(f"Failed to upsert batch. Error: {e}")
                
                # Check for empty sparse vectors in this batch to help debugging
                for record in batch:
                    sparse = record.get("sparse_values")
                    if sparse is not None:
                        if not sparse.get("indices") or not sparse.get("values"):
                            source_file = record.get("metadata", {}).get("source_file", "unknown")
                            chunk_text = record.get("metadata", {}).get("text", "")
                            logger.error(
                                f"FOUND EMPTY SPARSE VECTOR! "
                                f"File: {source_file} | Chunk ID: {record['id']} | "
                                f"Text snippet: {repr(chunk_text[:100])}"
                            )
                raise  # Re-raise to maintain original behavior
        
        return len(records)

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
        self._require_index()
        
        kwargs = {
            "top_k": top_k,
            "include_metadata": True,
            "include_values": include_values,
            "namespace": self.settings.pinecone_namespace,
            "filter": metadata_filter,
        }
        
        if query_text.strip() and alpha < 1.0:
            sparse = self.bm25.encode_queries(query_text)
            dense_scaled, sparse_scaled = hybrid_convex_scale(query_vector, sparse, alpha)
            kwargs["vector"] = dense_scaled
            kwargs["sparse_vector"] = sparse_scaled
        else:
            kwargs["vector"] = query_vector

        response = self.index.query(**kwargs)
        results = []
        seen_ids = set()
        for match in response.matches:
            if match.id in seen_ids:
                continue
            seen_ids.add(match.id)
            if match.score < score_threshold:
                continue
            metadata = dict(match.metadata or {})
            values = getattr(match, "values", None)
            results.append(
                _metadata_to_search_result(
                    metadata,
                    score=float(match.score),
                    vector=list(values) if include_values and values else None,
                )
            )
        return results

    def search_by_ahash(
        self,
        image_path_or_hash: str,
        max_distance: int = 5,
    ) -> list[SearchResult]:
        """
        Find indexed visuals whose aHash is within Hamming distance of the query.

        Args:
            image_path_or_hash: Image file path, or a hex aHash string.
            max_distance: Maximum Hamming distance to keep (0 = exact).
        """
        self._require_index()
        path = Path(image_path_or_hash)
        if path.is_file():
            query_hash = compute_ahash(path)
        else:
            query_hash = image_path_or_hash.strip()
        if not query_hash:
            return []

        # Use a near-zero vector to bypass Pinecone's zero-vector restriction and rapidly fetch metadata
        query_vector = [1e-5] * self.settings.embedding_dimension
        try:
            response = self.index.query(
                vector=query_vector,
                top_k=10000,
                include_metadata=True,
                namespace=self.settings.pinecone_namespace,
                filter={"content_type": {"$in": ["image", "chart", "table", "figure"]}}
            )
            metadata_list = [dict(match.metadata or {}) for match in response.matches]
        except Exception:
            metadata_list = list(self._iter_metadata(require_ahash=True))

        matches: list[SearchResult] = []
        for metadata in metadata_list:
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

    def get_stats(self) -> dict[str, object]:
        """Return vector counts and indexed source files for the active namespace."""
        self._require_index()
        stats = self.index.describe_index_stats()
        namespaces = getattr(stats, "namespaces", None)
        if namespaces is None and isinstance(stats, dict):
            namespaces = stats.get("namespaces", {})
        ns_info = (namespaces or {}).get(self.settings.pinecone_namespace, {})
        if hasattr(ns_info, "vector_count"):
            vector_count = int(ns_info.vector_count)
        elif isinstance(ns_info, dict):
            vector_count = int(ns_info.get("vector_count", 0))
        else:
            vector_count = 0

        source_files: set[str] = set()
        text_chunks = 0
        visual_chunks = 0
        for metadata in self._iter_metadata(require_ahash=False):
            source_files.add(str(metadata.get("source_file", "unknown")))
            if metadata.get("image_path") or metadata.get("ahash"):
                visual_chunks += 1
            else:
                text_chunks += 1

        return {
            "namespace": self.settings.pinecone_namespace,
            "index_name": self.settings.pinecone_index_name,
            "vector_count": vector_count,
            "text_chunks": text_chunks,
            "visual_chunks": visual_chunks,
            "source_files": sorted(source_files),
        }

    def _iter_metadata(self, require_ahash: bool = False) -> Iterable[dict]:
        """Yield metadata dicts for vectors in the active namespace."""
        for _vector_id, metadata in self._iter_records():
            if require_ahash and not metadata.get("ahash"):
                continue
            yield metadata

    def _iter_records(self) -> Iterable[tuple[str, dict]]:
        """Yield (vector_id, metadata) pairs for vectors in the active namespace."""
        namespace = self.settings.pinecone_namespace
        for page in self.index.list(namespace=namespace):
            ids = [
                str(item.id)
                for item in (page.vectors or [])
                if getattr(item, "id", None)
            ]
            if not ids:
                continue
            fetched = self.index.fetch(ids=ids, namespace=namespace)
            vectors = getattr(fetched, "vectors", None)
            if vectors is None and isinstance(fetched, dict):
                vectors = fetched.get("vectors", {})
            for vector_id, record in (vectors or {}).items():
                metadata = getattr(record, "metadata", None)
                if metadata is None and isinstance(record, dict):
                    metadata = record.get("metadata", {})
                yield str(vector_id), dict(metadata or {})

    def _require_index(self) -> None:
        if self.index is None:
            raise RuntimeError("Call connect() before using the vector store")


def _batches(items: list[dict], size: int) -> Iterable[list[dict]]:
    for start in range(0, len(items), size):
        yield items[start : start + size]
