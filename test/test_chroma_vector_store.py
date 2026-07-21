"""Tests for the ChromaDB vector store backend."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.config import Settings
from src.models import DocumentChunk, SearchResult
from src.vector_store_chroma import ChromaDBVectorStore


@pytest.fixture
def settings():
    """Minimal settings for testing (no Pinecone keys needed)."""
    return Settings(
        openai_api_key="test-key",
        embedding_api_key="test-key",
        embedding_dimension=4,
        vector_db_backend="chromadb",
    )


@pytest.fixture
def chroma_store(settings, tmp_path):
    """Create a ChromaDBVectorStore using a temp directory."""
    with patch(
        "src.vector_store_chroma._DEFAULT_PERSIST_DIR", str(tmp_path / "chroma_db")
    ):
        store = ChromaDBVectorStore(settings)
        store.connect(create_if_missing=True)
        yield store


def _make_chunks(n: int, source_file: str = "test.pdf") -> list[DocumentChunk]:
    return [
        DocumentChunk(
            id=f"chunk-{i}",
            text=f"This is test chunk number {i} about topic {i % 3}.",
            source_file=source_file,
            page=i + 1,
            content_type="text",
            heading=f"Section {i}",
            chunk_index=i,
        )
        for i in range(n)
    ]


def _make_vectors(n: int, dim: int = 4) -> list[list[float]]:
    """Generate simple but distinct vectors."""
    return [[float(i + j) / (n + dim) for j in range(dim)] for i in range(n)]


class TestChromaDBConnect:
    def test_connect_creates_collection(self, chroma_store):
        assert chroma_store._collection is not None
        assert chroma_store.backend_name == "chromadb"

    def test_require_collection_before_connect(self, settings):
        store = ChromaDBVectorStore(settings)
        with pytest.raises(RuntimeError, match="connect"):
            store.get_stats()


class TestChromaDBUpsert:
    def test_upsert_basic(self, chroma_store):
        chunks = _make_chunks(3)
        vectors = _make_vectors(3)
        count = chroma_store.upsert(chunks, vectors)
        assert count == 3

    def test_upsert_mismatched_lengths(self, chroma_store):
        chunks = _make_chunks(3)
        vectors = _make_vectors(2)
        with pytest.raises(ValueError, match="same length"):
            chroma_store.upsert(chunks, vectors)

    def test_upsert_idempotent(self, chroma_store):
        chunks = _make_chunks(2)
        vectors = _make_vectors(2)
        chroma_store.upsert(chunks, vectors)
        chroma_store.upsert(chunks, vectors)  # same IDs
        stats = chroma_store.get_stats()
        assert stats["vector_count"] == 2  # no duplicates


class TestChromaDBSearch:
    def test_search_returns_results(self, chroma_store):
        chunks = _make_chunks(5)
        vectors = _make_vectors(5)
        chroma_store.upsert(chunks, vectors)

        query_vector = [0.1, 0.2, 0.3, 0.4]
        results = chroma_store.search(
            query_vector=query_vector,
            top_k=3,
            score_threshold=0.0,
        )
        assert len(results) <= 3
        assert all(isinstance(r, SearchResult) for r in results)

    def test_search_score_threshold(self, chroma_store):
        chunks = _make_chunks(3)
        vectors = _make_vectors(3)
        chroma_store.upsert(chunks, vectors)

        # Very high threshold should filter out most/all results.
        results = chroma_store.search(
            query_vector=[0.1, 0.2, 0.3, 0.4],
            top_k=10,
            score_threshold=0.99,
        )
        # Results above the threshold may or may not exist; just verify filtering.
        for r in results:
            assert r.score >= 0.99

    def test_search_empty_collection(self, chroma_store):
        results = chroma_store.search(
            query_vector=[0.1, 0.2, 0.3, 0.4],
            top_k=5,
            score_threshold=0.0,
        )
        assert results == []

    def test_search_with_metadata_filter(self, chroma_store):
        chunks = _make_chunks(5)
        vectors = _make_vectors(5)
        chroma_store.upsert(chunks, vectors)

        results = chroma_store.search(
            query_vector=[0.1, 0.2, 0.3, 0.4],
            top_k=10,
            score_threshold=0.0,
            metadata_filter={"content_type": {"$eq": "text"}},
        )
        for r in results:
            assert r.content_type == "text"


class TestChromaDBDelete:
    def test_delete_source(self, chroma_store):
        chunks = _make_chunks(4, source_file="alpha.pdf")
        vectors = _make_vectors(4)
        chroma_store.upsert(chunks, vectors)

        other_chunks = _make_chunks(2, source_file="beta.pdf")
        other_chunks = [
            DocumentChunk(
                id=f"other-{i}",
                text=c.text,
                source_file="beta.pdf",
                page=c.page,
                content_type=c.content_type,
                heading=c.heading,
                chunk_index=c.chunk_index,
            )
            for i, c in enumerate(other_chunks)
        ]
        other_vectors = _make_vectors(2)
        chroma_store.upsert(other_chunks, other_vectors)

        deleted = chroma_store.delete_source("alpha.pdf")
        assert deleted == 4
        stats = chroma_store.get_stats()
        assert stats["vector_count"] == 2
        assert "beta.pdf" in stats["source_files"]
        assert "alpha.pdf" not in stats["source_files"]

    def test_delete_nonexistent_source(self, chroma_store):
        deleted = chroma_store.delete_source("nonexistent.pdf")
        assert deleted == 0


class TestChromaDBStats:
    def test_stats_empty(self, chroma_store):
        stats = chroma_store.get_stats()
        assert stats["vector_count"] == 0
        assert stats["source_files"] == []
        assert stats["index_name"] == "chromadb-local"

    def test_stats_with_data(self, chroma_store):
        chunks = _make_chunks(3)
        vectors = _make_vectors(3)
        chroma_store.upsert(chunks, vectors)

        stats = chroma_store.get_stats()
        assert stats["vector_count"] == 3
        assert "test.pdf" in stats["source_files"]
        assert stats["text_chunks"] == 3


class TestChromaDBSearchByAHash:
    def test_ahash_search_empty(self, chroma_store):
        results = chroma_store.search_by_ahash("abcdef0123456789")
        assert results == []

    def test_ahash_search_with_match(self, chroma_store):
        chunk = DocumentChunk(
            id="img-1",
            text="[table] Revenue table on page 1",
            source_file="report.pdf",
            page=1,
            content_type="visual",
            ahash="abcdef0123456789",
            image_path="/tmp/page_1_table.png",
        )
        chroma_store.upsert([chunk], [[0.1, 0.2, 0.3, 0.4]])

        results = chroma_store.search_by_ahash("abcdef0123456789", max_distance=0)
        assert len(results) == 1
        assert results[0].ahash == "abcdef0123456789"
        assert results[0].score == 1.0  # exact match


class TestVectorStoreFactory:
    def test_factory_chromadb(self, settings, tmp_path):
        with patch(
            "src.vector_store_chroma._DEFAULT_PERSIST_DIR",
            str(tmp_path / "chroma_db"),
        ):
            from src.vector_store_factory import create_vector_store

            store = create_vector_store(settings, backend="chromadb")
            assert store.backend_name == "chromadb"

    def test_factory_auto_fallback(self, settings, tmp_path):
        """When Pinecone key is present but connection fails, fall back to ChromaDB."""
        from dataclasses import replace

        settings_with_key = replace(settings, pinecone_api_key="invalid-key")
        with patch(
            "src.vector_store_chroma._DEFAULT_PERSIST_DIR",
            str(tmp_path / "chroma_db"),
        ):
            from src.vector_store_factory import create_vector_store

            store = create_vector_store(settings_with_key, backend="auto")
            assert store.backend_name == "chromadb"

    def test_factory_auto_no_key(self, settings, tmp_path):
        """When no Pinecone key, directly use ChromaDB."""
        from dataclasses import replace

        settings_no_key = replace(settings, pinecone_api_key="")
        with patch(
            "src.vector_store_chroma._DEFAULT_PERSIST_DIR",
            str(tmp_path / "chroma_db"),
        ):
            from src.vector_store_factory import create_vector_store

            store = create_vector_store(settings_no_key, backend="auto")
            assert store.backend_name == "chromadb"
