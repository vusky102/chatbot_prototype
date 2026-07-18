from __future__ import annotations

from dataclasses import replace

import streamlit as st

from src.config import Settings
from src.ingest.chunking import CHUNK_STRATEGIES

TUNING_KEYS = (
    "chunk_size",
    "chunk_overlap",
    "chunk_strategy",
    "retrieval_top_k",
    "retrieval_score_threshold",
    "retrieval_dedup_enabled",
    "retrieval_dedup_threshold",
    "retrieval_candidate_multiplier",
    "visual_provider",
)


def tuning_from_settings(settings: Settings) -> dict[str, object]:
    """Copy tunable RAG fields from settings into a plain dict."""
    return {key: getattr(settings, key) for key in TUNING_KEYS}


def init_tuning_state(base: Settings) -> None:
    """Ensure `st.session_state.rag_tuning` exists, seeded from base settings."""
    if "rag_tuning" not in st.session_state:
        st.session_state.rag_tuning = tuning_from_settings(base)


def get_effective_settings(base: Settings) -> Settings:
    """Merge base `.env` settings with the current Admin tuning overrides."""
    init_tuning_state(base)
    overrides = {key: st.session_state.rag_tuning[key] for key in TUNING_KEYS}
    return replace(base, **overrides)


def tuning_fingerprint(settings: Settings) -> tuple[object, ...]:
    """Stable tuple of tuning values used as a Streamlit cache key."""
    return tuple(getattr(settings, key) for key in TUNING_KEYS)


def validate_tuning(values: dict[str, object]) -> str | None:
    """Validate admin tuning form values; return an error message or None."""
    chunk_size = int(values["chunk_size"])
    chunk_overlap = int(values["chunk_overlap"])
    if chunk_size <= 0:
        return "Chunk size must be greater than 0."
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        return "Chunk overlap must be between 0 and chunk size."
    if str(values["chunk_strategy"]) not in CHUNK_STRATEGIES:
        return f"Chunk strategy must be one of {list(CHUNK_STRATEGIES)}."

    top_k = int(values["retrieval_top_k"])
    if top_k < 1:
        return "Top K must be at least 1."

    threshold = float(values["retrieval_score_threshold"])
    if threshold < 0.0 or threshold > 1.0:
        return "Score threshold must be between 0 and 1."

    dedup_threshold = float(values["retrieval_dedup_threshold"])
    if dedup_threshold < 0.0:
        return "Dedup threshold must be 0 or greater."

    multiplier = int(values["retrieval_candidate_multiplier"])
    if multiplier < 1:
        return "Candidate multiplier must be at least 1."

    provider = str(values["visual_provider"]).strip().lower()
    if provider not in {"gemini", "openai"}:
        return "Visual provider must be gemini or openai."
    return None
