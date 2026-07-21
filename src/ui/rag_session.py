from __future__ import annotations

from dataclasses import replace

import streamlit as st

from src.config import Settings
from src.rag import RAGService
from src.ui.tuning import get_effective_settings, tuning_fingerprint


@st.cache_resource(show_spinner=False)
def get_base_settings() -> Settings:
    """Load immutable settings from environment (cached)."""
    return Settings.from_env()


@st.cache_resource(show_spinner=False)
def _cached_rag_service(
    chat_model: str,
    chunk_size: int,
    chunk_overlap: int,
    chunk_strategy: str,
    retrieval_top_k: int,
    retrieval_score_threshold: float,
    retrieval_dedup_enabled: bool,
    retrieval_dedup_threshold: float,
    retrieval_candidate_multiplier: int,
    retrieval_hybrid_alpha: float,
    visual_provider: str,
    vector_db_backend: str,
) -> RAGService:
    """Build a RAGService keyed by the admin tuning fingerprint."""
    base = get_base_settings()
    settings = replace(
        base,
        chat_model=chat_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        chunk_strategy=chunk_strategy,
        retrieval_top_k=retrieval_top_k,
        retrieval_score_threshold=retrieval_score_threshold,
        retrieval_dedup_enabled=retrieval_dedup_enabled,
        retrieval_dedup_threshold=retrieval_dedup_threshold,
        retrieval_candidate_multiplier=retrieval_candidate_multiplier,
        retrieval_hybrid_alpha=retrieval_hybrid_alpha,
        visual_provider=visual_provider,
        vector_db_backend=vector_db_backend,
    )
    settings.validate_for_vector_store()
    return RAGService(settings)


def get_rag_service() -> RAGService:
    """Return the RAG service for current base settings + UI tuning overrides."""
    effective = get_effective_settings(get_base_settings())
    return _cached_rag_service(*tuning_fingerprint(effective))


def clear_rag_service_cache() -> None:
    """Drop cached RAG services after ingest/tuning changes that need a rebuild."""
    _cached_rag_service.clear()
