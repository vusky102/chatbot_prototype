from src.config import Settings
from src.lc.chain import LangChainGroundedGenerator
from src.lc.retriever import LangChainSemanticRetriever
from src.models import SearchResult
from src.rag.retriever import format_context


class RAGService:
    """Facade for retrieve + grounded answer generation used by UI and CLI."""

    def __init__(self, settings: Settings | None = None):
        """Wire retriever and generator from settings (or `.env` defaults)."""
        self.settings = settings or Settings.from_env()
        self.retriever = LangChainSemanticRetriever(self.settings)
        self.generator = LangChainGroundedGenerator(self.settings)

    def retrieve(self, query: str) -> list[SearchResult]:
        """Semantic search over indexed PDF chunks."""
        return self.retriever.search(query)

    def retrieve_image_by_hash(
        self,
        image_path_or_hash: str,
        max_distance: int = 5,
    ) -> list[SearchResult]:
        """Find indexed visuals by average-hash distance."""
        return self.retriever.search_image_by_hash(
            image_path_or_hash,
            max_distance=max_distance,
        )

    def stats(self) -> dict[str, object]:
        """Return vector-store index statistics."""
        return self.retriever.store.get_stats()

    def delete_source(self, source_file: str) -> int:
        """Delete all vectors for a source file; return deleted count."""
        return self.retriever.store.delete_source(source_file)

    def retrieve_as_text(self, query: str) -> str:
        """Retrieve chunks and format them as a single context string."""
        return format_context(self.retrieve(query))

    def answer(
        self,
        question: str,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, object]:
        """Retrieve context and generate a grounded answer with source metadata."""
        results = self.retrieve(question)
        answer = self.generator.generate(question, results, history=history)
        sources = [
            {
                "source_file": result.source_file,
                "page": result.page,
                "heading": result.heading,
                "content_type": result.content_type,
                "score": result.score,
                "image_path": result.image_path,
                "ahash": result.ahash,
            }
            for result in results
        ]
        return {"answer": answer, "sources": sources}
