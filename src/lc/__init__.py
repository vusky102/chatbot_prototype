"""LangChain adapters for the RAG workshop pipeline (stages 1–4).

Import submodules directly, e.g. `from src.lc.splitters import chunk_extracted_text_lc`,
to avoid eager circular imports with `src.rag`.
"""

__all__ = [
    "build_answer_chain",
    "build_embeddings",
    "LangChainSemanticRetriever",
    "chunk_extracted_text_lc",
    "LangChainPineconeVectorStore",
]


def __getattr__(name: str):
    if name == "build_answer_chain":
        from src.lc.chain import build_answer_chain

        return build_answer_chain
    if name == "build_embeddings":
        from src.lc.embeddings import build_embeddings

        return build_embeddings
    if name == "LangChainSemanticRetriever":
        from src.lc.retriever import LangChainSemanticRetriever

        return LangChainSemanticRetriever
    if name == "chunk_extracted_text_lc":
        from src.lc.splitters import chunk_extracted_text_lc

        return chunk_extracted_text_lc
    if name == "LangChainPineconeVectorStore":
        from src.lc.vectorstore import LangChainPineconeVectorStore

        return LangChainPineconeVectorStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
