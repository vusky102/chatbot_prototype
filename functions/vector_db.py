"""
PDF-to-ChromaDB Vector Store.

Provides a PDFVectorStore class that:
  - Extracts text from PDFs using existing pdf_text_extraction utilities
  - Chunks text with configurable strategies (page / fixed / paragraph)
  - Embeds chunks using existing embedding() function (text-embedding-3-small)
  - Stores embeddings in ChromaDB for semantic retrieval
  - Extracts images via AI-powered image_extraction pipeline
  - Computes aHash (average perceptual hash) for each extracted image
  - Enables precise image retrieval via Hamming distance matching

Usage:
    from functions import PDFVectorStore

    store = PDFVectorStore(collection_name="my_docs", persist_directory="./chroma_db")
    store.import_pdf("docs/example.pdf", chunk_strategy="fixed", chunk_size=1000)

    results = store.search("What is the leave policy?", n_results=5)
    image_matches = store.search_image_by_hash("output/example/page_1_table_1.png", max_distance=5)
"""

import os
import re
import uuid
from pathlib import Path

from scipy.spatial.distance import cosine as cosine_distance

import chromadb
import imagehash
from PIL import Image

from .embedding import embedding
from .pdf_text_extraction import extract_text_from_pdf
from .image_extraction import extract_images


# ─── Chunking Helpers ────────────────────────────────────────────────────────

def _parse_pages(text):
    """
    Split extracted PDF text into per-page segments using the
    <!-- Page: N --> markers inserted by extract_text_from_pdf().

    Returns:
        list of dict: [{"page": int, "text": str}, ...]
    """
    pattern = r"<!-- Page: (\d+) -->"
    parts = re.split(pattern, text)

    pages = []
    # parts alternates: [pre-text, page_num, page_text, page_num, page_text, ...]
    # The first element (index 0) is text before the first marker (usually empty).
    i = 1
    while i < len(parts) - 1:
        page_num = int(parts[i])
        page_text = parts[i + 1].strip()
        if page_text:
            pages.append({"page": page_num, "text": page_text})
        i += 2

    return pages


def _chunk_by_page(text):
    """
    Strategy: 'page' — one chunk per PDF page.

    Best for:
        - Short documents (< 5 pages)
        - Documents where each page is a self-contained topic
    """
    pages = _parse_pages(text)
    return [
        {"text": p["text"], "page": p["page"]}
        for p in pages
    ]


def _chunk_by_fixed(text, chunk_size=1000, chunk_overlap=200):
    """
    Strategy: 'fixed' — fixed-size character windows with overlap.

    Best for:
        - General documents, long-form text
        - Default: chunk_size=1000, overlap=200

    Recommendations by document type (documented in import_pdf docstring):
        General documents:    chunk_size=1000, overlap=200
        Legal / policy docs:  chunk_size=1500, overlap=300
        Technical manuals:    chunk_size=800,  overlap=150
    """
    pages = _parse_pages(text)

    # Concatenate all page texts with page boundary markers for tracking
    segments = []
    for p in pages:
        segments.append({"page": p["page"], "text": p["text"]})

    chunks = []
    for seg in segments:
        seg_text = seg["text"]
        page_num = seg["page"]
        start = 0

        while start < len(seg_text):
            end = start + chunk_size
            chunk_text = seg_text[start:end].strip()
            if chunk_text:
                chunks.append({"text": chunk_text, "page": page_num})
            start += chunk_size - chunk_overlap

    return chunks


def _chunk_by_paragraph(text, chunk_size=1200):
    """
    Strategy: 'paragraph' — split on double-newlines, merge small paragraphs
    up to chunk_size.

    Best for:
        - Well-structured documents with clear paragraph breaks
        - Reports, articles, proposals
    """
    pages = _parse_pages(text)
    chunks = []

    for p in pages:
        paragraphs = re.split(r"\n\s*\n", p["text"])
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If adding this paragraph exceeds chunk_size, flush current chunk
            if current_chunk and len(current_chunk) + len(para) + 2 > chunk_size:
                chunks.append({"text": current_chunk.strip(), "page": p["page"]})
                current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Flush remaining content
        if current_chunk.strip():
            chunks.append({"text": current_chunk.strip(), "page": p["page"]})

    return chunks


CHUNK_STRATEGIES = {
    "page": _chunk_by_page,
    "fixed": _chunk_by_fixed,
    "paragraph": _chunk_by_paragraph,
}


# ─── aHash Helpers ───────────────────────────────────────────────────────────

def compute_ahash(image_path):
    """
    Compute the average perceptual hash (aHash) for an image file.

    Returns:
        str: Hexadecimal hash string (e.g. 'f8f8f0e0c0808080')
    """
    img = Image.open(image_path)
    return str(imagehash.average_hash(img))


def hamming_distance(hash1, hash2):
    """
    Compute Hamming distance between two hex hash strings.
    Lower distance = more similar images.
    0 = identical, typically < 5 = very similar.
    """
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    return h1 - h2


# ─── PDF Vector Store ────────────────────────────────────────────────────────

class PDFVectorStore:
    """
    A ChromaDB-backed vector store for PDF documents.

    Supports:
        - Text extraction, chunking, embedding, and semantic search
        - Image extraction with aHash perceptual hashing for precise retrieval

    Args:
        collection_name (str): Name of the ChromaDB collection for text chunks.
            A companion '{collection_name}_images' collection is created for images.
        persist_directory (str | None): If provided, ChromaDB data is persisted
            to this directory. If None, an ephemeral in-memory store is used.
    """

    def __init__(self, collection_name="pdf_documents", persist_directory=None):
        self.collection_name = collection_name

        if persist_directory:
            persist_path = Path(persist_directory).resolve()
            persist_path.mkdir(parents=True, exist_ok=True)
            self._client = chromadb.PersistentClient(path=str(persist_path))
            print(f"[VectorDB] Persistent ChromaDB initialized at: {persist_path}")
        else:
            self._client = chromadb.Client()
            print("[VectorDB] Ephemeral (in-memory) ChromaDB initialized.")

        # Text chunks collection
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        # Image metadata collection
        self._image_collection = self._client.get_or_create_collection(
            name=f"{collection_name}_images",
            metadata={"hnsw:space": "cosine"}
        )

        print(f"[VectorDB] Collections ready: '{collection_name}' (text), "
              f"'{collection_name}_images' (images)")

    # ── Text Import ──────────────────────────────────────────────────────

    def import_pdf(
        self,
        pdf_path,
        chunk_strategy="fixed",
        chunk_size=1000,
        chunk_overlap=200,
        extract_images_flag=True,
        image_provider=None,
        image_output_dir="output",
    ):
        """
        Import a PDF into the vector store.

        Extracts text, chunks it with the chosen strategy, generates embeddings,
        and stores everything in ChromaDB. Optionally extracts images with AI
        and computes aHash for each.

        Args:
            pdf_path (str): Path to the PDF file.
            chunk_strategy (str): Chunking strategy — 'page', 'fixed', or 'paragraph'.
            chunk_size (int): Max characters per chunk (for 'fixed' and 'paragraph').
            chunk_overlap (int): Character overlap between chunks (for 'fixed' only).
            extract_images_flag (bool): Whether to run the image extraction pipeline.
            image_provider (str | None): AI provider for image extraction
                ('openai', 'gemini', or None for auto-detect).
            image_output_dir (str): Directory for extracted image files.

        Chunking Strategy Recommendations:
            ┌─────────────────────────┬────────────┬────────────┬─────────┐
            │ Document Type           │ Strategy   │ chunk_size │ overlap │
            ├─────────────────────────┼────────────┼────────────┼─────────┤
            │ General documents       │ 'fixed'    │ 1000       │ 200     │
            │ Legal / policy docs     │ 'fixed'    │ 1500       │ 300     │
            │ Short brochures (<5pp)  │ 'page'     │ —          │ —       │
            │ Structured reports      │ 'paragraph'│ 1200       │ —       │
            │ Technical manuals       │ 'fixed'    │ 800        │ 150     │
            └─────────────────────────┴────────────┴────────────┴─────────┘

        Returns:
            dict: Summary with keys 'text_chunks', 'images_indexed', 'source_pdf'.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        pdf_name = pdf_path.name
        print(f"\n{'='*60}")
        print(f"[VectorDB] Importing: {pdf_name}")
        print(f"  Strategy: {chunk_strategy} | chunk_size: {chunk_size} | overlap: {chunk_overlap}")
        print(f"{'='*60}")

        # ── Deduplication: Remove existing data for this PDF ──
        # This ensures reimporting the same file (even with different chunk
        # parameters) produces a clean result without orphaned old chunks.
        existing_text = self._collection.get(
            where={"source_pdf": pdf_name},
            include=[],
        )
        existing_images = self._image_collection.get(
            where={"source_pdf": pdf_name},
            include=[],
        )

        if existing_text["ids"]:
            self._collection.delete(ids=existing_text["ids"])
            print(f"[VectorDB] Removed {len(existing_text['ids'])} existing text chunks for '{pdf_name}'.")

        if existing_images["ids"]:
            self._image_collection.delete(ids=existing_images["ids"])
            print(f"[VectorDB] Removed {len(existing_images['ids'])} existing image records for '{pdf_name}'.")

        # ── Step 1: Extract text ──
        print("[VectorDB] Step 1/4: Extracting text from PDF...")
        full_text = extract_text_from_pdf(str(pdf_path))

        if not full_text or not full_text.strip():
            print("[VectorDB] Warning: No text extracted from PDF.")
            return {"text_chunks": 0, "images_indexed": 0, "source_pdf": pdf_name}

        # ── Step 2: Chunk text ──
        print(f"[VectorDB] Step 2/4: Chunking text (strategy='{chunk_strategy}')...")
        if chunk_strategy not in CHUNK_STRATEGIES:
            raise ValueError(
                f"Unknown chunk strategy '{chunk_strategy}'. "
                f"Available: {list(CHUNK_STRATEGIES.keys())}"
            )

        chunk_fn = CHUNK_STRATEGIES[chunk_strategy]
        if chunk_strategy == "fixed":
            chunks = chunk_fn(full_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        elif chunk_strategy == "paragraph":
            chunks = chunk_fn(full_text, chunk_size=chunk_size)
        else:  # "page"
            chunks = chunk_fn(full_text)

        if not chunks:
            print("[VectorDB] Warning: Chunking produced no segments.")
            return {"text_chunks": 0, "images_indexed": 0, "source_pdf": pdf_name}

        print(f"  → {len(chunks)} chunks created.")

        # ── Step 3: Embed and store text chunks ──
        print("[VectorDB] Step 3/4: Generating embeddings and indexing text chunks...")
        batch_size = 20  # OpenAI API batch limit for embeddings
        total_indexed = 0

        for batch_start in range(0, len(chunks), batch_size):
            batch = chunks[batch_start:batch_start + batch_size]
            texts = [c["text"] for c in batch]

            embeddings_list = embedding(texts)

            ids = [str(uuid.uuid4()) for _ in batch]
            metadatas = [
                {
                    "source_pdf": pdf_name,
                    "page": c["page"],
                    "chunk_strategy": chunk_strategy,
                    "chunk_index": batch_start + i,
                }
                for i, c in enumerate(batch)
            ]

            self._collection.add(
                ids=ids,
                embeddings=embeddings_list,
                documents=texts,
                metadatas=metadatas,
            )
            total_indexed += len(batch)
            print(f"  → Indexed {total_indexed}/{len(chunks)} chunks...", end="\r")

        print(f"  → Indexed {total_indexed}/{len(chunks)} chunks. Done.")

        # ── Step 4: Image extraction + aHash ──
        images_indexed = 0
        if extract_images_flag:
            print("[VectorDB] Step 4/4: Extracting images and computing aHash...")
            try:
                img_result = extract_images(
                    pdf_path=str(pdf_path),
                    output_dir=image_output_dir,
                    provider=image_provider,
                )

                output_dir = img_result.get("output_dir")
                if output_dir and Path(output_dir).exists():
                    images_indexed = self._index_images(
                        image_dir=output_dir,
                        source_pdf=pdf_name,
                        full_text=full_text,
                    )
                else:
                    print("  → No images extracted or output directory not found.")

            except Exception as e:
                print(f"  → Image extraction failed: {e}")
                print("  → Continuing without image indexing.")
        else:
            print("[VectorDB] Step 4/4: Image extraction skipped (extract_images_flag=False).")

        print(f"\n[VectorDB] Import complete: {total_indexed} text chunks, "
              f"{images_indexed} images indexed from '{pdf_name}'.")

        return {
            "text_chunks": total_indexed,
            "images_indexed": images_indexed,
            "source_pdf": pdf_name,
        }

    def _index_images(self, image_dir, source_pdf, full_text=""):
        """
        Scan an image output directory, compute aHash for each image,
        generate a combined embedding from the image metadata + co-located text,
        and store in the images collection.
        """
        image_dir = Path(image_dir)
        image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
        image_files = [
            f for f in image_dir.iterdir()
            if f.suffix.lower() in image_extensions
        ]

        if not image_files:
            print("  → No image files found in output directory.")
            return 0

        indexed = 0
        pages_text = {p["page"]: p["text"] for p in _parse_pages(full_text)}

        for img_path in image_files:
            try:
                # Parse metadata from filename: page_N_type_idx.ext
                fname = img_path.stem
                parts = fname.split("_")

                page_num = 0
                element_type = "unknown"
                if len(parts) >= 3 and parts[0] == "page":
                    try:
                        page_num = int(parts[1])
                    except ValueError:
                        pass
                    # Type is the third part (e.g., "table", "chart", "embedded")
                    element_type = parts[2] if len(parts) > 2 else "unknown"

                # Compute aHash
                ahash = compute_ahash(str(img_path))

                # Build description for embedding:
                # Combine structural metadata + co-located page text excerpt
                description_parts = [
                    f"[{element_type}] Image from page {page_num} of {source_pdf}."
                ]

                # Add co-located text from the same page (truncated for embedding)
                co_located_text = pages_text.get(page_num, "")
                if co_located_text:
                    # Take first 500 chars of the page text as context
                    excerpt = co_located_text[:500].strip()
                    description_parts.append(f"Page context: {excerpt}")

                combined_description = " ".join(description_parts)

                # Generate embedding from the combined description
                emb = embedding([combined_description])[0]

                # Store in images collection
                self._image_collection.add(
                    ids=[str(uuid.uuid4())],
                    embeddings=[emb],
                    documents=[combined_description],
                    metadatas=[{
                        "ahash": ahash,
                        "type": element_type,
                        "page": page_num,
                        "source_pdf": source_pdf,
                        "image_path": str(img_path.resolve()),
                        "filename": img_path.name,
                    }],
                )
                indexed += 1
                print(f"  → [{element_type}] {img_path.name} | aHash: {ahash}")

            except Exception as e:
                print(f"  → Failed to index {img_path.name}: {e}")

        print(f"  → {indexed} images indexed with aHash.")
        return indexed

    # ── Semantic Search ──────────────────────────────────────────────────

    def search(self, query, n_results=5, deduplicate=True, dedup_threshold=0.05):
        """
        Perform semantic search over indexed text chunks.

        When the same content exists across multiple PDFs, query-time
        deduplication filters out near-identical results so the caller
        receives diverse, relevant content.

        Args:
            query (str): Natural language search query.
            n_results (int): Number of top results to return.
            deduplicate (bool): If True, remove results whose embeddings
                are too similar to an already-selected result. This handles
                duplicate content across different PDFs without deleting
                any stored data.
            dedup_threshold (float): Maximum cosine distance between two
                result embeddings to consider them duplicates. Lower values
                are stricter. Default 0.05 (~95% similarity).

        Returns:
            list of dict: Each dict contains 'text', 'distance', 'metadata'.
        """
        collection_count = self._collection.count()
        if collection_count == 0:
            return []

        query_emb = embedding([query])[0]

        # Fetch extra candidates when deduplicating, so we still have
        # enough results after filtering out duplicates.
        fetch_count = min(
            n_results * 3 if deduplicate else n_results,
            collection_count,
        )

        results = self._collection.query(
            query_embeddings=[query_emb],
            n_results=fetch_count,
            include=["documents", "distances", "metadatas", "embeddings"],
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return []

        # Build candidate list
        candidates = []
        for i in range(len(results["documents"][0])):
            candidates.append({
                "text": results["documents"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
                "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                "_embedding": results["embeddings"][0][i] if results.get("embeddings") else None,
            })

        if not deduplicate:
            # Strip internal embedding before returning
            for c in candidates[:n_results]:
                c.pop("_embedding", None)
            return candidates[:n_results]

        # ── Query-time deduplication ──
        # Greedily select results: for each candidate (already sorted by
        # relevance), keep it only if it is sufficiently different from all
        # previously selected results.
        selected = []
        for candidate in candidates:
            if len(selected) >= n_results:
                break

            emb = candidate.get("_embedding")
            if emb is None:
                # Cannot deduplicate without embeddings; keep the candidate
                selected.append(candidate)
                continue

            is_duplicate = False
            for kept in selected:
                kept_emb = kept.get("_embedding")
                if kept_emb is not None:
                    dist = cosine_distance(emb, kept_emb)
                    if dist < dedup_threshold:
                        is_duplicate = True
                        break

            if not is_duplicate:
                selected.append(candidate)

        # Strip internal embedding before returning
        for s in selected:
            s.pop("_embedding", None)

        return selected

    # ── Image Hash Retrieval ─────────────────────────────────────────────

    def search_image_by_hash(self, image_path_or_hash, max_distance=5):
        """
        Find images in the store that match a given image by aHash similarity.

        This enables precise table/chart retrieval: given a reference screenshot,
        find the exact (or near-exact) same visual element across all indexed PDFs.

        Args:
            image_path_or_hash (str): Either a file path to an image, or a hex
                aHash string directly.
            max_distance (int): Maximum Hamming distance to consider a match.
                0 = exact match only, 5 = very similar, 10 = loosely similar.

        Returns:
            list of dict: Matching images with keys 'image_path', 'ahash',
                'hamming_distance', 'type', 'page', 'source_pdf', 'filename'.
        """
        # Determine the query hash
        if os.path.isfile(image_path_or_hash):
            query_hash = compute_ahash(image_path_or_hash)
        else:
            query_hash = image_path_or_hash

        # Retrieve all image metadata from the collection
        count = self._image_collection.count()
        if count == 0:
            return []

        all_records = self._image_collection.get(
            include=["metadatas"],
            limit=count,
        )

        matches = []
        for i, meta in enumerate(all_records["metadatas"]):
            stored_hash = meta.get("ahash", "")
            if not stored_hash:
                continue

            dist = hamming_distance(query_hash, stored_hash)
            if dist <= max_distance:
                matches.append({
                    "image_path": meta.get("image_path", ""),
                    "ahash": stored_hash,
                    "hamming_distance": dist,
                    "type": meta.get("type", "unknown"),
                    "page": meta.get("page", 0),
                    "source_pdf": meta.get("source_pdf", ""),
                    "filename": meta.get("filename", ""),
                })

        # Sort by Hamming distance (closest first)
        matches.sort(key=lambda x: x["hamming_distance"])
        return matches

    # ── Utilities ────────────────────────────────────────────────────────

    def get_stats(self):
        """
        Return statistics about the current vector store.

        Returns:
            dict: Collection counts, indexed PDFs list.
        """
        text_count = self._collection.count()
        image_count = self._image_collection.count()

        # Get unique source PDFs
        source_pdfs = set()
        if text_count > 0:
            all_meta = self._collection.get(include=["metadatas"], limit=text_count)
            for meta in all_meta.get("metadatas", []):
                source_pdfs.add(meta.get("source_pdf", "unknown"))

        return {
            "text_chunks": text_count,
            "images_indexed": image_count,
            "source_pdfs": sorted(source_pdfs),
            "collection_name": self.collection_name,
        }

    def clear(self):
        """Delete all documents from both text and image collections."""
        # ChromaDB doesn't have a clear() method — delete and recreate
        self._client.delete_collection(self.collection_name)
        self._client.delete_collection(f"{self.collection_name}_images")

        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._image_collection = self._client.get_or_create_collection(
            name=f"{self.collection_name}_images",
            metadata={"hnsw:space": "cosine"}
        )
        print("[VectorDB] All collections cleared.")
