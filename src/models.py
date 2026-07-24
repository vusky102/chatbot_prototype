from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DocumentChunk:
    id: str
    text: str
    source_file: str
    page: int
    content_type: str = "text"
    heading: str = ""
    image_path: str = ""
    ahash: str = ""
    chunk_index: int = 0

    def metadata(self) -> dict[str, Any]:
        def _truncate_str(text: str, max_bytes: int = 30000) -> str:
            if not text:
                return text
            encoded = text.encode("utf-8")
            if len(encoded) <= max_bytes:
                return text
            # Truncate safely, ignoring partial multi-byte characters at the boundary
            return encoded[:max_bytes].decode("utf-8", "ignore")

        data: dict[str, Any] = {
            "text": _truncate_str(self.text),
            "source_file": self.source_file,
            "page": self.page,
            "content_type": self.content_type,
            "heading": self.heading,
            "chunk_index": self.chunk_index,
        }
        if self.image_path:
            # Prevent base64 strings masquerading as paths from breaking the limit
            data["image_path"] = _truncate_str(self.image_path, max_bytes=8000)
        if self.ahash:
            data["ahash"] = self.ahash
        return data


@dataclass(frozen=True)
class SearchResult:
    text: str
    score: float
    source_file: str
    page: int
    content_type: str
    heading: str = ""
    image_path: str = ""
    ahash: str = ""
    raw_metadata: dict[str, Any] = field(default_factory=dict)
    # Populated only during retrieval when query-time dedup needs vectors.
    vector: list[float] | None = None

    @property
    def citation(self) -> str:
        location = f"{self.source_file}, page {self.page}"
        if self.heading:
            location += f", {self.heading}"
        return location
