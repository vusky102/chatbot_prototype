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

    def answer_with_image(
        self,
        image_path_or_hash: str,
        question: str = "",
        history: list[dict[str, str]] | None = None,
        max_distance: int = 12,
    ) -> dict[str, object]:
        """Retrieve context from visual similarity, caption semantics, and text query to generate a grounded answer."""
        image_results = self.retrieve_image_by_hash(image_path_or_hash, max_distance=max_distance)

        # Generate a semantic caption for the uploaded image using the Vision model
        image_desc = ""
        from pathlib import Path
        path = Path(image_path_or_hash)
        if path.is_file():
            try:
                from src.ingest.visual_caption import VisualCaptioner
                captioner = VisualCaptioner(self.settings.visual_provider)
                if getattr(captioner, "client", None) is not None:
                     image_desc = captioner.caption(path)
            except Exception as exc:
                print(f"Warning: could not generate image caption: {exc}")

        # Combine text logic: retrieve from Pinecone based on user question AND image semantics
        search_query = f"{question.strip()}\n{image_desc.strip()}".strip()
        text_results = self.retrieve(search_query) if search_query else []

        seen = set()
        combined_results = []
        for r in image_results:
            key = (r.source_file, r.page, r.content_type, r.heading, r.text)
            if key not in seen:
                seen.add(key)
                combined_results.append(r)
        for r in text_results:
            key = (r.source_file, r.page, r.content_type, r.heading, r.text)
            if key not in seen:
                seen.add(key)
                combined_results.append(r)

        prompt_question = question.strip()
        if not prompt_question:
             # If the user uploaded an image without typing text, force a question so the LLM knows what to answer
             prompt_question = "Please analyze the uploaded image using the provided context and explain what it illustrates."

        if image_desc:
             prompt_question += f"\n\nUploaded Image Context:\n{image_desc}"

        answer = self.generator.generate(prompt_question.strip(), combined_results, history=history)
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
            for result in combined_results
        ]
        return {"answer": answer, "sources": sources}

