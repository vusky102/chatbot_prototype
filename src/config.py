import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer") from error


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a number") from error


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = ""
    openai_base_url: str = ""
    chat_model: str = "gpt-4o-mini"
    embedding_api_key: str = ""
    embedding_base_url: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    pinecone_api_key: str = ""
    pinecone_index_name: str = "rag-chatbot"
    pinecone_namespace: str = "training-gd4"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    chunk_size: int = 800
    chunk_overlap: int = 150
    chunk_strategy: str = "heading"
    retrieval_top_k: int = 5
    retrieval_score_threshold: float = 0.3
    retrieval_dedup_enabled: bool = True
    retrieval_dedup_threshold: float = 0.05
    retrieval_candidate_multiplier: int = 3
    visual_provider: str = "gemini"
    visual_output_dir: str = "output/rag_visuals"

    @classmethod
    def from_env(cls) -> "Settings":
        openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        openai_base_url = os.getenv("OPENAI_API_BASEURL", "").strip()
        return cls(
            openai_api_key=openai_api_key,
            openai_base_url=openai_base_url,
            chat_model=os.getenv("OPENAI_API_MODEL", "gpt-4o-mini").strip(),
            embedding_api_key=(
                os.getenv("OPENAI_EMBEDDING_API_KEY") or openai_api_key
            ).strip(),
            embedding_base_url=(
                os.getenv("OPENAI_EMBEDDING_BASEURL") or openai_base_url
            ).strip(),
            embedding_model=os.getenv(
                "OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"
            ).strip(),
            embedding_dimension=_env_int("OPENAI_EMBEDDING_DIMENSION", 1536),
            pinecone_api_key=os.getenv("PINECONE_API_KEY", "").strip(),
            pinecone_index_name=os.getenv(
                "PINECONE_INDEX_NAME", "rag-chatbot"
            ).strip(),
            pinecone_namespace=os.getenv(
                "PINECONE_NAMESPACE", "training-gd4"
            ).strip(),
            pinecone_cloud=os.getenv("PINECONE_CLOUD", "aws").strip(),
            pinecone_region=os.getenv("PINECONE_REGION", "us-east-1").strip(),
            chunk_size=_env_int("RAG_CHUNK_SIZE", 800),
            chunk_overlap=_env_int("RAG_CHUNK_OVERLAP", 150),
            chunk_strategy=os.getenv("RAG_CHUNK_STRATEGY", "heading").strip().lower(),
            retrieval_top_k=_env_int("RAG_RETRIEVAL_TOP_K", 5),
            retrieval_score_threshold=_env_float(
                "RAG_RETRIEVAL_SCORE_THRESHOLD", 0.3
            ),
            retrieval_dedup_enabled=_env_bool("RAG_RETRIEVAL_DEDUP_ENABLED", True),
            retrieval_dedup_threshold=_env_float(
                "RAG_RETRIEVAL_DEDUP_THRESHOLD", 0.05
            ),
            retrieval_candidate_multiplier=_env_int(
                "RAG_RETRIEVAL_CANDIDATE_MULTIPLIER", 3
            ),
            visual_provider=os.getenv("RAG_VISUAL_PROVIDER", "gemini").strip(),
            visual_output_dir=os.getenv(
                "RAG_VISUAL_OUTPUT_DIR", "output/rag_visuals"
            ).strip(),
        )

    def validate_for_vector_store(self) -> None:
        from src.ingest.chunking import CHUNK_STRATEGIES

        missing = []
        if not self.embedding_api_key:
            missing.append("OPENAI_EMBEDDING_API_KEY or OPENAI_API_KEY")
        if not self.pinecone_api_key:
            missing.append("PINECONE_API_KEY")
        if missing:
            raise RuntimeError(
                "Missing required environment variables: " + ", ".join(missing)
            )
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("RAG_CHUNK_OVERLAP must be smaller than RAG_CHUNK_SIZE")
        if self.chunk_strategy not in CHUNK_STRATEGIES:
            raise ValueError(
                f"RAG_CHUNK_STRATEGY must be one of {list(CHUNK_STRATEGIES)}"
            )
