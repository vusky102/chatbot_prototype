"""Stage 1 — LangChain text splitters with workshop page/heading strategies."""

from __future__ import annotations

import hashlib
import re

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.ingest.chunking import CHUNK_STRATEGIES, PAGE_PATTERN, HEADING_PATTERN
from src.lc.documents import document_to_chunk
from src.models import DocumentChunk


def _stable_id(source_file: str, page: int, content_type: str, index: int) -> str:
    raw = f"{source_file}|{page}|{content_type}|{index}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _page_sections(extracted_text: str) -> list[tuple[int, str]]:
    matches = list(PAGE_PATTERN.finditer(extracted_text))
    sections = []
    for index, match in enumerate(matches):
        content_start = match.end()
        content_end = matches[index + 1].start() if index + 1 < len(matches) else None
        sections.append((int(match.group(1)), extracted_text[content_start:content_end]))
    if not sections and extracted_text.strip():
        sections.append((1, extracted_text))
    return sections


def _make_splitter(chunk_size: int, chunk_overlap: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        keep_separator=False,
    )


def _docs_from_pieces(
    pieces: list[str],
    *,
    source_file: str,
    page: int,
    heading: str,
    start_index: int,
) -> list[Document]:
    docs: list[Document] = []
    for offset, piece in enumerate(pieces):
        text = piece.strip()
        if not text:
            continue
        index = start_index + offset
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "id": _stable_id(source_file, page, "text", index),
                    "source_file": source_file,
                    "page": page,
                    "content_type": "text",
                    "heading": heading,
                    "chunk_index": index,
                },
            )
        )
    return docs


def _chunk_by_heading_lc(
    extracted_text: str,
    source_file: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    splitter = _make_splitter(chunk_size, chunk_overlap)
    docs: list[Document] = []
    global_index = 0
    for page, page_text in _page_sections(extracted_text):
        current_heading = ""
        section_lines: list[str] = []
        sections: list[tuple[str, str]] = []

        def flush_section() -> None:
            if section_lines:
                sections.append((current_heading, "\n".join(section_lines)))
                section_lines.clear()

        for line in page_text.splitlines():
            heading_match = HEADING_PATTERN.match(line.strip())
            if heading_match:
                flush_section()
                current_heading = heading_match.group(2).strip()
                section_lines.append(line.strip())
            else:
                section_lines.append(line)
        flush_section()

        for heading, section_text in sections:
            pieces = splitter.split_text(section_text)
            batch = _docs_from_pieces(
                pieces,
                source_file=source_file,
                page=page,
                heading=heading,
                start_index=global_index,
            )
            docs.extend(batch)
            global_index += len(batch)
    return docs


def _chunk_by_page_lc(extracted_text: str, source_file: str) -> list[Document]:
    docs: list[Document] = []
    for index, (page, page_text) in enumerate(_page_sections(extracted_text)):
        text = page_text.strip()
        if not text:
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "id": _stable_id(source_file, page, "text", index),
                    "source_file": source_file,
                    "page": page,
                    "content_type": "text",
                    "heading": "",
                    "chunk_index": index,
                },
            )
        )
    return docs


def _chunk_by_fixed_lc(
    extracted_text: str,
    source_file: str,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    splitter = _make_splitter(chunk_size, chunk_overlap)
    docs: list[Document] = []
    global_index = 0
    for page, page_text in _page_sections(extracted_text):
        pieces = splitter.split_text(page_text)
        batch = _docs_from_pieces(
            pieces,
            source_file=source_file,
            page=page,
            heading="",
            start_index=global_index,
        )
        docs.extend(batch)
        global_index += len(batch)
    return docs


def _chunk_by_paragraph_lc(
    extracted_text: str,
    source_file: str,
    chunk_size: int,
) -> list[Document]:
    docs: list[Document] = []
    global_index = 0
    for page, page_text in _page_sections(extracted_text):
        current = ""
        for para in re.split(r"\n\s*\n", page_text):
            para = para.strip()
            if not para:
                continue
            if current and len(current) + len(para) + 2 > chunk_size:
                docs.append(
                    Document(
                        page_content=current.strip(),
                        metadata={
                            "id": _stable_id(source_file, page, "text", global_index),
                            "source_file": source_file,
                            "page": page,
                            "content_type": "text",
                            "heading": "",
                            "chunk_index": global_index,
                        },
                    )
                )
                global_index += 1
                current = para
            else:
                current = f"{current}\n\n{para}" if current else para
        if current.strip():
            docs.append(
                Document(
                    page_content=current.strip(),
                    metadata={
                        "id": _stable_id(source_file, page, "text", global_index),
                        "source_file": source_file,
                        "page": page,
                        "content_type": "text",
                        "heading": "",
                        "chunk_index": global_index,
                    },
                )
            )
            global_index += 1
    return docs


def split_extracted_text_to_documents(
    extracted_text: str,
    source_file: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    chunk_strategy: str = "heading",
) -> list[Document]:
    """Stage 1 public API: return LangChain Documents."""
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be between 0 and chunk_size")

    strategy = (chunk_strategy or "heading").strip().lower()
    if strategy not in CHUNK_STRATEGIES:
        raise ValueError(
            f"Unknown chunk strategy '{chunk_strategy}'. "
            f"Available: {list(CHUNK_STRATEGIES)}"
        )

    if strategy == "page":
        return _chunk_by_page_lc(extracted_text, source_file)
    if strategy == "fixed":
        return _chunk_by_fixed_lc(
            extracted_text, source_file, chunk_size, chunk_overlap
        )
    if strategy == "paragraph":
        return _chunk_by_paragraph_lc(extracted_text, source_file, chunk_size)
    return _chunk_by_heading_lc(
        extracted_text, source_file, chunk_size, chunk_overlap
    )


def chunk_extracted_text_lc(
    extracted_text: str,
    source_file: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
    chunk_strategy: str = "heading",
) -> list[DocumentChunk]:
    """Stage 1 adapter: LangChain Documents → workshop DocumentChunk."""
    docs = split_extracted_text_to_documents(
        extracted_text,
        source_file,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_strategy=chunk_strategy,
    )
    return [document_to_chunk(doc, chunk_index=i) for i, doc in enumerate(docs)]
