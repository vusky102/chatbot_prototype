from pathlib import Path


def resolve_image_path(image_path: str, visual_output_dir: str) -> Path | None:
    """Resolve image_path (absolute or relative) to an existing file, or None."""
    p = Path(image_path)
    # Case 1: Old absolute path that still exists
    if p.is_absolute() and p.is_file():
        return p
    # Case 2: New relative path — resolve against visual_output_dir
    resolved = Path(visual_output_dir) / p
    if resolved.is_file():
        return resolved
    return None
