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
        data: dict[str, Any] = {
            "text": self.text,
            "source_file": self.source_file,
            "page": self.page,
            "content_type": self.content_type,
            "heading": self.heading,
            "chunk_index": self.chunk_index,
        }
        if self.image_path:
            data["image_path"] = self.image_path
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
