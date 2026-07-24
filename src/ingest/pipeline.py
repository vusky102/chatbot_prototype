import re
from pathlib import Path

from src.config import Settings
from src.ingest.chunking import chunk_extracted_text, page_text_map
from src.ingest.image_extraction import extract_images
from src.ingest.pdf_text_extraction import extract_text_from_pdf
from src.ingest.visual_caption import caption_visuals
from src.lc.embeddings import build_embeddings
from src.lc.vectorstore import LangChainVectorStoreAdapter
from src.models import DocumentChunk


def _collect_visual_chunks(
    pdf_path: Path,
    settings: Settings,
    extracted_text: str,
) -> list[DocumentChunk]:
    """Extract visuals, caption them, and return visual `DocumentChunk`s."""
    try:
        result = extract_images(
            pdf_path=str(pdf_path),
            output_dir=settings.visual_output_dir,
            provider=settings.visual_provider,
        )
    except Exception as exc:
        print(f"  -> Warning: image extraction failed: {exc}")
        print("  -> Continuing without visual indexing.")
        return []

    if result.get("error"):
        print(f"  -> Warning: image extraction reported an error: {result['error']}")

    output_dir = result.get("output_dir")
    visual_dir = Path(output_dir) if output_dir else None
    if visual_dir is None or not visual_dir.exists():
        print("  -> No visual output directory found; skipping captions.")
        return []

    try:
        return caption_visuals(
            visual_dir=visual_dir,
            source_file=pdf_path.name,
            provider=settings.visual_provider,
            page_texts=page_text_map(extracted_text),
            elements=result.get("elements"),
            visual_output_dir_base=Path(settings.visual_output_dir),
        )
    except Exception as exc:
        print(f"  -> Warning: visual captioning failed: {exc}")
        print("  -> Continuing without visual indexing.")
        return []


def build_chunks(
    pdf_path: str | Path,
    settings: Settings,
    include_visuals: bool = True,
) -> list[DocumentChunk]:
    """Extract text (+ optional visuals) from a PDF into indexable chunks."""
    pdf_path = Path(pdf_path)
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    extracted_text = extract_text_from_pdf(str(pdf_path))
    chunks = chunk_extracted_text(
        extracted_text=extracted_text,
        source_file=pdf_path.name,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        chunk_strategy=settings.chunk_strategy,
    )

    if include_visuals:
        chunks.extend(_collect_visual_chunks(pdf_path, settings, extracted_text))

    # Filter out garbage text chunks (e.g. chunks that only contain punctuation/whitespace like '.')
    # This prevents the `[400] Sparse vector must contain at least one value` error in Pinecone.
    valid_chunks = []
    for chunk in chunks:
        if chunk.content_type == "text" and not bool(re.search(r'[a-zA-Z0-9]', chunk.text)):
            continue
        valid_chunks.append(chunk)

    return valid_chunks


def ingest_pdf(
    pdf_path: str | Path,
    settings: Settings | None = None,
    include_visuals: bool = True,
) -> dict[str, int | str]:
    """Chunk a PDF and upsert its vectors into Pinecone (replacing prior source)."""
    settings = settings or Settings.from_env()
    settings.validate_for_vector_store()
    chunks = build_chunks(pdf_path, settings, include_visuals=include_visuals)
    if not chunks:
        raise RuntimeError(f"No content could be extracted from {pdf_path}")

    embeddings = build_embeddings(settings)
    store = LangChainVectorStoreAdapter(
        settings,
        embeddings,
        create_if_missing=True,
    )
    source_file = Path(pdf_path).name
    store.delete_source(source_file)
    upserted = store.add_chunks(chunks)
    text_chunks = sum(chunk.content_type == "text" for chunk in chunks)
    visual_chunks = len(chunks) - text_chunks
    return {
        "source_file": source_file,
        "text_chunks": text_chunks,
        "visual_chunks": visual_chunks,
        "upserted": upserted,
        "chunk_strategy": settings.chunk_strategy,
    }
