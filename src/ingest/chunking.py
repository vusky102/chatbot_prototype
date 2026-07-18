"""Text chunking facade — page markers + LangChain splitters (stage 1)."""

from __future__ import annotations

import re

from src.models import DocumentChunk


PAGE_PATTERN = re.compile(r"<!--\s*Page:\s*(\d+)\s*-->")
HEADING_PATTERN = re.compile(r"^(#{1,4})\s+(.+)$")

CHUNK_STRATEGIES = ("heading", "page", "fixed", "paragraph")


def _page_sections(extracted_text: str) -> list[tuple[int, str]]:
    """Split marker-annotated PDF text into (page_number, page_body) pairs."""
    matches = list(PAGE_PATTERN.finditer(extracted_text))
    sections = []
    for index, match in enumerate(matches):
        content_start = match.end()
        content_end = matches[index + 1].start() if index + 1 < len(matches) else None
        sections.append((int(match.group(1)), extracted_text[content_start:content_end]))
    if not sections and extracted_text.strip():
        sections.append((1, extracted_text))
    return sections


def page_text_map(extracted_text: str) -> dict[int, str]:
    """Map page number -> raw page text from `<!-- Page: N -->` markers."""
    return {
        page: text.strip()
        for page, text in _page_sections(extracted_text)
        if text.strip()
    }


def chunk_extracted_text(
    extracted_text: str,
    source_file: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    chunk_strategy: str = "heading",
) -> list[DocumentChunk]:
    """Split extracted PDF text into chunks (LangChain stage 1)."""
    # Lazy import avoids circular dependency with src.lc.splitters.
    from src.lc.splitters import chunk_extracted_text_lc

    return chunk_extracted_text_lc(
        extracted_text,
        source_file,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_strategy=chunk_strategy,
    )
