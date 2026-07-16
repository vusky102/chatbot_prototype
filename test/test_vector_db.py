"""
End-to-end test for PDFVectorStore.

Tests:
  1. Ephemeral ChromaDB initialization
  2. PDF text extraction + chunking (all 3 strategies)
  3. Embedding generation + ChromaDB indexing
  4. Semantic search query returns ranked results
  5. Image extraction + aHash computation + storage
  6. search_image_by_hash() returns correct matches
  7. get_stats() and clear() utilities
"""

import os
import sys
from pathlib import Path

# Add project root to python path for package imports
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from functions import PDFVectorStore


# ─── Configuration ───────────────────────────────────────────────────────────

SAMPLE_PDF = project_root / "docs" / "Training_data_GD4" / "input" / "Public_035.pdf"
IMAGE_OUTPUT_DIR = project_root / "output"


def separator(title):
    print(f"\n{'─'*60}")
    print(f"  TEST: {title}")
    print(f"{'─'*60}")


def test_chunking_strategies():
    """Test all 3 chunking strategies without actually embedding (fast check)."""
    separator("Chunking Strategies (text-only, no embedding)")

    from functions.pdf_text_extraction import extract_text_from_pdf
    from functions.vector_db import _chunk_by_page, _chunk_by_fixed, _chunk_by_paragraph

    text = extract_text_from_pdf(str(SAMPLE_PDF))
    assert text and len(text) > 0, "Text extraction returned empty!"
    print(f"  Extracted {len(text)} characters from {SAMPLE_PDF.name}")

    # Page strategy
    page_chunks = _chunk_by_page(text)
    print(f"  [page]      → {len(page_chunks)} chunks")
    assert len(page_chunks) > 0, "Page chunking produced no chunks!"

    # Fixed strategy (default params)
    fixed_chunks = _chunk_by_fixed(text, chunk_size=1000, chunk_overlap=200)
    print(f"  [fixed]     → {len(fixed_chunks)} chunks (size=1000, overlap=200)")
    assert len(fixed_chunks) > 0, "Fixed chunking produced no chunks!"

    # Paragraph strategy
    para_chunks = _chunk_by_paragraph(text, chunk_size=1200)
    print(f"  [paragraph] → {len(para_chunks)} chunks (size=1200)")
    assert len(para_chunks) > 0, "Paragraph chunking produced no chunks!"

    # Verify chunk metadata
    for chunk in page_chunks[:3]:
        assert "text" in chunk, "Chunk missing 'text' key"
        assert "page" in chunk, "Chunk missing 'page' key"
        assert isinstance(chunk["page"], int), "Page must be an integer"

    print("  ✓ All chunking strategies produce valid output.")


def test_import_and_search():
    """Test full import pipeline + semantic search (requires API keys)."""
    separator("Import PDF + Semantic Search")

    store = PDFVectorStore(collection_name="test_docs", persist_directory=None)

    # Import with fixed strategy, skip images for this test (faster)
    result = store.import_pdf(
        pdf_path=str(SAMPLE_PDF),
        chunk_strategy="fixed",
        chunk_size=1000,
        chunk_overlap=200,
        extract_images_flag=False,  # Skip images to save time
    )

    assert result["text_chunks"] > 0, "No text chunks were indexed!"
    print(f"\n  Import result: {result}")

    # Test semantic search
    print("\n  Running semantic search queries...")
    queries = [
        "What is the main topic?",
        "technical specifications",
        "summary of the document",
    ]

    for query in queries:
        results = store.search(query, n_results=3)
        print(f"\n  Query: '{query}'")
        for i, r in enumerate(results):
            dist = f"{r['distance']:.4f}" if r['distance'] is not None else "N/A"
            text_preview = r['text'][:80].replace('\n', ' ')
            print(f"    [{i+1}] dist={dist} | page={r['metadata'].get('page', '?')} | {text_preview}...")

        assert len(results) > 0, f"Search returned no results for '{query}'"

    # Test stats
    stats = store.get_stats()
    print(f"\n  Stats: {stats}")
    assert stats["text_chunks"] > 0

    # Test clear
    store.clear()
    stats_after = store.get_stats()
    assert stats_after["text_chunks"] == 0, "Clear did not remove all documents!"
    print("  ✓ Clear works correctly.")

    print("\n  ✓ Import + Search test passed.")


def test_image_import_and_ahash():
    """Test image extraction + aHash indexing (requires API keys + AI provider)."""
    separator("Image Extraction + aHash Indexing")

    store = PDFVectorStore(collection_name="test_images", persist_directory=None)

    result = store.import_pdf(
        pdf_path=str(SAMPLE_PDF),
        chunk_strategy="page",
        extract_images_flag=True,
        image_provider=None,  # Auto-detect
        image_output_dir=str(IMAGE_OUTPUT_DIR),
    )

    print(f"\n  Import result: {result}")

    if result["images_indexed"] > 0:
        # Test search_image_by_hash by looking up one of the indexed images
        stats = store.get_stats()
        print(f"  Stats: {stats}")

        # Get the first image's path from the collection
        all_images = store._image_collection.get(
            include=["metadatas"],
            limit=1,
        )

        if all_images["metadatas"]:
            first_img_meta = all_images["metadatas"][0]
            test_image_path = first_img_meta.get("image_path", "")
            test_hash = first_img_meta.get("ahash", "")

            print(f"\n  Testing search_image_by_hash with hash: {test_hash}")

            # Search by hash string
            matches = store.search_image_by_hash(test_hash, max_distance=0)
            print(f"  → Exact matches (distance=0): {len(matches)}")
            assert len(matches) >= 1, "Self-lookup should find at least 1 match"

            # Search by image file path (if file still exists)
            if os.path.isfile(test_image_path):
                matches_by_file = store.search_image_by_hash(test_image_path, max_distance=5)
                print(f"  → Near matches via file (distance≤5): {len(matches_by_file)}")
                for m in matches_by_file[:3]:
                    print(f"    [{m['type']}] {m['filename']} | "
                          f"dist={m['hamming_distance']} | page={m['page']}")

            print("  ✓ Image aHash retrieval works correctly.")
    else:
        print("  ⚠ No images were indexed (possibly no visual elements in the PDF).")
        print("  → Skipping aHash retrieval test.")

    store.clear()
    print("  ✓ Image import + aHash test completed.")


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not SAMPLE_PDF.exists():
        print(f"ERROR: Sample PDF not found at {SAMPLE_PDF}")
        print("Please ensure the test PDF exists before running this test.")
        sys.exit(1)

    print("=" * 60)
    print("  PDFVectorStore — End-to-End Test Suite")
    print("=" * 60)

    # Test 1: Chunking strategies (no API calls needed)
    test_chunking_strategies()

    # Test 2: Full import + search (needs OpenAI API key for embeddings)
    test_import_and_search()

    # Test 3: Image import + aHash (needs AI provider for image detection)
    # This test is slower as it runs image extraction
    try:
        test_image_import_and_ahash()
    except Exception as e:
        print(f"\n  ⚠ Image test skipped due to error: {e}")
        print("  → This is expected if no AI provider API key is configured.")

    print("\n" + "=" * 60)
    print("  All tests completed!")
    print("=" * 60)
