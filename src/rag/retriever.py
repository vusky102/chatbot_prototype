from dataclasses import replace
from math import sqrt

from src.models import SearchResult


def cosine_distance(left: list[float], right: list[float]) -> float:
    """Return 1 - cosine similarity. Lower means more similar."""
    if not left or not right or len(left) != len(right):
        return 1.0
    dot = 0.0
    left_norm = 0.0
    right_norm = 0.0
    for a, b in zip(left, right):
        dot += a * b
        left_norm += a * a
        right_norm += b * b
    if left_norm <= 0.0 or right_norm <= 0.0:
        return 1.0
    return 1.0 - (dot / (sqrt(left_norm) * sqrt(right_norm)))


def deduplicate_results(
    candidates: list[SearchResult],
    top_k: int,
    dedup_threshold: float,
) -> list[SearchResult]:
    """
    Greedy query-time dedup for near-duplicate retrieved chunks.

    Candidates are assumed sorted by relevance (highest score first). Keep a
    candidate only when its embedding is sufficiently different from every
    already selected result (cosine distance >= threshold).
    """
    if top_k <= 0:
        return []

    selected: list[SearchResult] = []
    for candidate in candidates:
        if len(selected) >= top_k:
            break

        emb = candidate.vector
        if emb is None:
            selected.append(candidate)
            continue

        is_duplicate = False
        for kept in selected:
            kept_emb = kept.vector
            if kept_emb is None:
                continue
            if cosine_distance(emb, kept_emb) < dedup_threshold:
                is_duplicate = True
                break

        if not is_duplicate:
            selected.append(candidate)

    # Drop vectors before returning context to the LLM.
    return [replace(item, vector=None) for item in selected]


def format_context(results: list[SearchResult]) -> str:
    """Format retrieved chunks into a single LLM context string."""
    if not results:
        return "No relevant information was found in the knowledge base."

    sections = []
    for index, result in enumerate(results, 1):
        sections.append(
            f"[Source {index}: {result.citation}; "
            f"type={result.content_type}; score={result.score:.3f}]\n"
            f"{result.text}"
        )
    return "\n\n".join(sections)
