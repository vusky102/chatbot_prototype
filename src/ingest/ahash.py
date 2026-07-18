"""Average perceptual hash (aHash) helpers for visual retrieval."""

from pathlib import Path

import imagehash
from PIL import Image


def compute_ahash(image_path: str | Path) -> str:
    """
    Compute the average perceptual hash (aHash) for an image file.

    Returns:
        Hexadecimal hash string (e.g. 'f8f8f0e0c0808080').
    """
    with Image.open(image_path) as img:
        return str(imagehash.average_hash(img))


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Hamming distance between two hex aHash strings.
    Lower is more similar: 0 = identical, typically < 5 = very similar.
    """
    left = imagehash.hex_to_hash(hash1)
    right = imagehash.hex_to_hash(hash2)
    return left - right
