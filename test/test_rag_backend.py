import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.config import Settings
from src.ingest.chunking import chunk_extracted_text
from src.models import SearchResult
from src.rag.retriever import cosine_distance, deduplicate_results, format_context
from src.vector_store import PineconeVectorStore


class ChunkingTests(unittest.TestCase):
    def test_preserves_page_and_heading_metadata(self):
        text = """
<!-- Page: 1 -->
# First topic
Alpha content for the first page.
<!-- Page: 2 -->
## Second topic
Beta content for the second page.
"""
        chunks = chunk_extracted_text(
            text,
            source_file="sample.pdf",
            chunk_size=100,
            chunk_overlap=10,
        )

        self.assertEqual([chunk.page for chunk in chunks], [1, 2])
        self.assertEqual(chunks[0].heading, "First topic")
        self.assertEqual(chunks[1].heading, "Second topic")
        self.assertEqual(chunks[0].source_file, "sample.pdf")

    def test_ids_are_stable(self):
        kwargs = {
            "extracted_text": "<!-- Page: 1 -->\nA short paragraph.",
            "source_file": "sample.pdf",
            "chunk_size": 100,
            "chunk_overlap": 10,
        }
        first = chunk_extracted_text(**kwargs)
        second = chunk_extracted_text(**kwargs)
        self.assertEqual(first[0].id, second[0].id)

    def test_rejects_invalid_overlap(self):
        with self.assertRaises(ValueError):
            chunk_extracted_text("text", "sample.pdf", 100, 100)


class ContextFormattingTests(unittest.TestCase):
    def test_formats_citation_and_content_type(self):
        result = SearchResult(
            text="y = ax + b",
            score=0.91,
            source_file="Public_035.pdf",
            page=2,
            content_type="formula",
            heading="Model",
        )
        context = format_context([result])
        self.assertIn("Public_035.pdf, page 2, Model", context)
        self.assertIn("type=formula", context)
        self.assertIn("y = ax + b", context)

    def test_empty_results_return_not_found(self):
        self.assertIn("No relevant information", format_context([]))


class SettingsTests(unittest.TestCase):
    def test_separate_embedding_credentials_override_chat_credentials(self):
        values = {
            "OPENAI_API_KEY": "chat-key",
            "OPENAI_API_BASEURL": "https://chat.example/v1",
            "OPENAI_EMBEDDING_API_KEY": "embedding-key",
            "OPENAI_EMBEDDING_BASEURL": "https://embedding.example/v1",
        }
        with patch.dict("os.environ", values, clear=False):
            settings = Settings.from_env()
        self.assertEqual(settings.embedding_api_key, "embedding-key")
        self.assertEqual(
            settings.embedding_base_url, "https://embedding.example/v1"
        )


class VectorStoreTests(unittest.TestCase):
    def _store_with_stats(self, namespaces):
        store = PineconeVectorStore.__new__(PineconeVectorStore)
        store.settings = Settings(pinecone_namespace="training-gd4")
        store.index = MagicMock()
        store.index.describe_index_stats.return_value = SimpleNamespace(
            namespaces=namespaces
        )
        return store

    def test_delete_source_skips_missing_namespace(self):
        store = self._store_with_stats({})
        store._iter_records = MagicMock(return_value=[])
        deleted = store.delete_source("Public_035.pdf")
        self.assertEqual(deleted, 0)
        # Falls back to filter delete when no IDs are listed.
        store.index.delete.assert_called_once_with(
            namespace="training-gd4",
            filter={"source_file": {"$eq": "Public_035.pdf"}},
        )

    def test_delete_source_filters_existing_namespace(self):
        store = self._store_with_stats({"training-gd4": {}})
        store._iter_records = MagicMock(
            return_value=[
                ("id-1", {"source_file": "Public_035.pdf"}),
                ("id-2", {"source_file": "other.pdf"}),
                ("id-3", {"source_file": "Public_035.pdf"}),
            ]
        )
        deleted = store.delete_source("Public_035.pdf")
        self.assertEqual(deleted, 2)
        store.index.delete.assert_called_once_with(
            ids=["id-1", "id-3"],
            namespace="training-gd4",
            async_req=True,
        )

    def test_search_deduplicates_eventually_consistent_matches(self):
        store = self._store_with_stats({"training-gd4": {}})
        metadata = {
            "text": "linear regression",
            "source_file": "Public_035.pdf",
            "page": 1,
            "content_type": "text",
        }
        match = SimpleNamespace(
            id="same-id",
            score=0.4,
            metadata=metadata,
            values=None,
        )
        store.index.query.return_value = SimpleNamespace(matches=[match, match])
        results = store.search([], top_k=5, score_threshold=0.3)
        self.assertEqual(len(results), 1)

    def test_iter_metadata_reads_list_response_ids(self):
        from pinecone.models.vectors.responses import ListItem, ListResponse

        store = PineconeVectorStore.__new__(PineconeVectorStore)
        store.settings = Settings(pinecone_namespace="training-gd4")
        store.index = MagicMock()
        store.index.list.return_value = [
            ListResponse(
                vectors=[
                    ListItem(id="chunk-1"),
                    ListItem(id="chunk-2"),
                ]
            )
        ]
        store.index.fetch.return_value = SimpleNamespace(
            vectors={
                "chunk-1": SimpleNamespace(
                    metadata={"source_file": "Public_035.pdf", "text": "alpha"}
                ),
                "chunk-2": SimpleNamespace(
                    metadata={"source_file": "Public_036.pdf", "text": "beta"}
                ),
            }
        )

        metadata = list(store._iter_metadata())
        self.assertEqual(
            {item["source_file"] for item in metadata},
            {"Public_035.pdf", "Public_036.pdf"},
        )
        store.index.fetch.assert_called_once_with(
            ids=["chunk-1", "chunk-2"],
            namespace="training-gd4",
        )


class QueryTimeDedupTests(unittest.TestCase):
    def _result(self, text, score, vector):
        return SearchResult(
            text=text,
            score=score,
            source_file="Public_035.pdf",
            page=1,
            content_type="text",
            vector=vector,
        )

    def test_cosine_distance_identical_vectors_is_zero(self):
        self.assertAlmostEqual(cosine_distance([1.0, 0.0], [1.0, 0.0]), 0.0)

    def test_drops_near_duplicate_embeddings(self):
        primary = self._result("alpha", 0.9, [1.0, 0.0, 0.0])
        near_duplicate = self._result("alpha copy", 0.88, [0.999, 0.001, 0.0])
        diverse = self._result("beta", 0.8, [0.0, 1.0, 0.0])

        selected = deduplicate_results(
            [primary, near_duplicate, diverse],
            top_k=2,
            dedup_threshold=0.05,
        )

        self.assertEqual([item.text for item in selected], ["alpha", "beta"])
        self.assertTrue(all(item.vector is None for item in selected))

    def test_keeps_candidates_when_vectors_missing(self):
        first = self._result("one", 0.9, None)
        second = self._result("two", 0.8, None)
        selected = deduplicate_results([first, second], top_k=2, dedup_threshold=0.05)
        self.assertEqual([item.text for item in selected], ["one", "two"])


class AHashTests(unittest.TestCase):
    def test_identical_images_have_zero_hamming_distance(self):
        from PIL import Image

        from src.ingest.ahash import compute_ahash, hamming_distance
        from src.models import DocumentChunk

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.png"
            Image.new("RGB", (32, 32), color=(20, 40, 60)).save(path)
            left = compute_ahash(path)
            right = compute_ahash(path)
            self.assertEqual(left, right)
            self.assertEqual(hamming_distance(left, right), 0)

            chunk = DocumentChunk(
                id="visual-1",
                text="caption",
                source_file="sample.pdf",
                page=1,
                content_type="table",
                image_path=str(path),
                ahash=left,
            )
            self.assertEqual(chunk.metadata()["ahash"], left)

    def test_search_by_ahash_filters_and_sorts(self):
        store = PineconeVectorStore.__new__(PineconeVectorStore)
        store.settings = Settings(pinecone_namespace="training-gd4")
        store.index = MagicMock()

        records = [
            {
                "text": "exact",
                "source_file": "a.pdf",
                "page": 1,
                "content_type": "table",
                "image_path": "a.png",
                "ahash": "ffffffffffffffff",
            },
            {
                "text": "close",
                "source_file": "b.pdf",
                "page": 2,
                "content_type": "chart",
                "image_path": "b.png",
                "ahash": "fffffffffffffffe",
            },
            {
                "text": "far",
                "source_file": "c.pdf",
                "page": 3,
                "content_type": "image",
                "image_path": "c.png",
                "ahash": "0000000000000000",
            },
        ]
        store._iter_metadata = MagicMock(return_value=records)

        matches = store.search_by_ahash("ffffffffffffffff", max_distance=2)
        self.assertEqual([item.text for item in matches], ["exact", "close"])
        self.assertEqual(matches[0].raw_metadata["hamming_distance"], 0)
        self.assertEqual(matches[1].raw_metadata["hamming_distance"], 1)
        self.assertEqual(matches[0].ahash, "ffffffffffffffff")


class LangChainStageTests(unittest.TestCase):
    def test_stage1_splitter_returns_documents(self):
        from langchain_core.documents import Document

        from src.lc.splitters import split_extracted_text_to_documents

        docs = split_extracted_text_to_documents(
            "<!-- Page: 1 -->\n# Topic\nHello world.",
            source_file="sample.pdf",
            chunk_strategy="heading",
            chunk_size=100,
            chunk_overlap=10,
        )
        self.assertTrue(docs)
        self.assertIsInstance(docs[0], Document)
        self.assertEqual(docs[0].metadata["source_file"], "sample.pdf")
        self.assertEqual(docs[0].metadata["page"], 1)

    def test_stage4_chain_builds(self):
        from src.lc.chain import build_answer_chain

        chain = build_answer_chain(
            Settings(openai_api_key="test-key", chat_model="gpt-4o-mini")
        )
        self.assertTrue(hasattr(chain, "invoke"))


class ChunkStrategyTests(unittest.TestCase):
    SAMPLE = """
<!-- Page: 1 -->
# Intro
First paragraph on page one.

Second paragraph still page one.
<!-- Page: 2 -->
## Details
Page two content here.
"""

    def test_page_strategy_one_chunk_per_page(self):
        chunks = chunk_extracted_text(
            self.SAMPLE,
            source_file="sample.pdf",
            chunk_strategy="page",
        )
        self.assertEqual(len(chunks), 2)
        self.assertEqual([chunk.page for chunk in chunks], [1, 2])

    def test_paragraph_strategy_merges_until_size(self):
        chunks = chunk_extracted_text(
            self.SAMPLE,
            source_file="sample.pdf",
            chunk_size=80,
            chunk_overlap=10,
            chunk_strategy="paragraph",
        )
        self.assertGreaterEqual(len(chunks), 2)
        self.assertTrue(all(chunk.content_type == "text" for chunk in chunks))

    def test_unknown_strategy_raises(self):
        with self.assertRaises(ValueError):
            chunk_extracted_text(
                self.SAMPLE,
                source_file="sample.pdf",
                chunk_strategy="nope",
            )


class VisualCaptionContextTests(unittest.TestCase):
    def test_builds_text_with_page_context_without_captioner(self):
        from PIL import Image

        from src.ingest.visual_caption import caption_visuals

        with tempfile.TemporaryDirectory() as tmp:
            visual_dir = Path(tmp)
            image_path = visual_dir / "page_2_table_1.png"
            Image.new("RGB", (32, 32), color=(10, 20, 30)).save(image_path)

            with patch(
                "src.ingest.visual_caption.VisualCaptioner",
                side_effect=RuntimeError("quota"),
            ):
                chunks = caption_visuals(
                    visual_dir=visual_dir,
                    source_file="sample.pdf",
                    provider="gemini",
                    page_texts={2: "Regression formula y = ax + b on this page."},
                )

        self.assertEqual(len(chunks), 1)
        self.assertIn("Page context:", chunks[0].text)
        self.assertIn("y = ax + b", chunks[0].text)
        self.assertIn("[table]", chunks[0].text)
        self.assertTrue(chunks[0].ahash)


class PipelineGracefulVisualTests(unittest.TestCase):
    def test_build_chunks_keeps_text_when_visuals_fail(self):
        from src.ingest import pipeline as pipeline_module

        settings = Settings(
            chunk_size=100,
            chunk_overlap=10,
            chunk_strategy="page",
            visual_provider="gemini",
            visual_output_dir="output/rag_visuals",
        )
        with tempfile.TemporaryDirectory() as tmp:
            pdf_path = Path(tmp) / "sample.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")

            with (
                patch.object(
                    pipeline_module,
                    "extract_text_from_pdf",
                    return_value="<!-- Page: 1 -->\nHello world text.",
                ),
                patch.object(
                    pipeline_module,
                    "extract_images",
                    side_effect=RuntimeError("gemini down"),
                ),
            ):
                chunks = pipeline_module.build_chunks(
                    pdf_path,
                    settings=settings,
                    include_visuals=True,
                )

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].content_type, "text")
        self.assertIn("Hello world", chunks[0].text)


if __name__ == "__main__":
    unittest.main()
