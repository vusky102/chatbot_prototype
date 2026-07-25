"""Markdown preparation helpers for chat messages."""

from __future__ import annotations

import re


def normalize_math_delimiters(text: str) -> str:
    """Convert common LaTeX delimiters to the form Streamlit/KaTeX supports."""
    if not text:
        return ""

    # Models commonly emit \(…\) and \[…\], while st.markdown documents
    # inline/display math as $…$ and $$…$$. Do not touch fenced code examples.
    parts = re.split(r"(```[\s\S]*?```)", text)
    for index in range(0, len(parts), 2):
        parts[index] = re.sub(
            r"\\\[\s*([\s\S]*?)\s*\\\]",
            r"\n\n$$\1$$\n\n",
            parts[index],
        )
        parts[index] = re.sub(r"\\\(([\s\S]*?)\\\)", r"$\1$", parts[index])
    return "".join(parts)
