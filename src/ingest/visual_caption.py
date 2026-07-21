import base64
import concurrent.futures
import hashlib
import json
import mimetypes
import re
from pathlib import Path

from src.ingest.ahash import compute_ahash
from src.ingest.image_extraction import get_gemini_client, get_openai_client
from src.models import DocumentChunk


VISUAL_NAME_PATTERN = re.compile(
    r"page_(?P<page>\d+)_(?P<type>embedded|table|chart|diagram|figure|formula|signature|other)"
)
CAPTION_PROMPT = """
Describe this visual element from a PDF accurately and in detail for semantic
search. Preserve all visible labels, values, formulas, legends and relationships.
For a table, return its data as Markdown. For a chart, explain axes, series and
important values. Do not infer information that is not visible. Respond in the
same language as the visual.
""".strip()
PAGE_CONTEXT_CHARS = 500


def _visual_id(source_file: str, image_name: str) -> str:
    raw = f"{source_file}|visual|{image_name}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


def _image_metadata(image_path: Path) -> tuple[int, str]:
    match = VISUAL_NAME_PATTERN.search(image_path.stem.lower())
    if not match:
        return 0, "image"
    content_type = match.group("type")
    if content_type in {"embedded", "figure", "other"}:
        content_type = "image"
    return int(match.group("page")), content_type


def _build_visual_text(
    content_type: str,
    page: int,
    source_file: str,
    caption: str,
    page_excerpt: str,
) -> str:
    parts = [f"[{content_type}] Image from page {page} of {source_file}."]
    if caption:
        parts.append(caption.strip())
    if page_excerpt:
        parts.append(f"Page context: {page_excerpt}")
    return " ".join(parts)


class VisualCaptioner:
    def __init__(self, provider: str):
        self.provider = provider.lower()
        if self.provider == "gemini":
            self.client, self.model = get_gemini_client()
        elif self.provider == "openai":
            self.client, self.model = get_openai_client()
        else:
            raise ValueError("Visual provider must be 'gemini' or 'openai'")

    def caption(self, image_path: Path) -> str:
        image_bytes = image_path.read_bytes()
        mime_type = mimetypes.guess_type(image_path.name)[0] or "image/png"
        if self.provider == "gemini":
            return self._caption_gemini(image_bytes, mime_type)
        return self._caption_openai(image_bytes, mime_type)

    def _caption_gemini(self, image_bytes: bytes, mime_type: str) -> str:
        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        types.Part.from_text(text=CAPTION_PROMPT),
                    ],
                )
            ],
            config=types.GenerateContentConfig(temperature=0.0),
        )
        return (response.text or "").strip()

    def _caption_openai(self, image_bytes: bytes, mime_type: str) -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CAPTION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{encoded}"
                            },
                        },
                    ],
                }
            ],
            temperature=0.0,
        )
        return (response.choices[0].message.content or "").strip()


def caption_visuals(
    visual_dir: Path,
    source_file: str,
    provider: str,
    page_texts: dict[int, str] | None = None,
) -> list[DocumentChunk]:
    if not visual_dir.exists():
        return []

    cache_path = visual_dir / "captions.json"
    cache = {}
    if cache_path.exists():
        cache = json.loads(cache_path.read_text(encoding="utf-8"))

    image_paths = sorted(
        path
        for path in visual_dir.iterdir()
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    if not image_paths:
        return []

    captioner = None
    try:
        captioner = VisualCaptioner(provider)
    except Exception as exc:
        print(f"  -> Warning: visual captioner unavailable ({exc}); using page context only.")

    page_texts = page_texts or {}
    chunks = []
    changed = False

    tasks = []
    for index, image_path in enumerate(image_paths):
        tasks.append({"index": index, "path": image_path, "caption": cache.get(image_path.name, "")})

    def _run_caption(task):
        if not task["caption"] and captioner is not None:
            try:
                task["caption"] = captioner.caption(task["path"])
            except Exception as exc:
                print(f"  -> Warning: caption failed for {task['path'].name}: {exc}")
                task["caption"] = ""
        return task

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_run_caption, tasks))

    for task in sorted(results, key=lambda x: x["index"]):
        index = task["index"]
        image_path = task["path"]
        caption = task["caption"]

        if caption and caption != cache.get(image_path.name, ""):
            cache[image_path.name] = caption
            changed = True

        page, content_type = _image_metadata(image_path)
        page_excerpt = ""
        co_located = page_texts.get(page, "")
        if co_located:
            page_excerpt = re.sub(r"\s+", " ", co_located).strip()[:PAGE_CONTEXT_CHARS]

        text = _build_visual_text(
            content_type=content_type,
            page=page,
            source_file=source_file,
            caption=caption,
            page_excerpt=page_excerpt,
        )
        try:
            ahash = compute_ahash(image_path)
        except Exception as exc:
            print(f"  -> Warning: aHash failed for {image_path.name}: {exc}")
            ahash = ""

        chunks.append(
            DocumentChunk(
                id=_visual_id(source_file, image_path.name),
                text=text,
                source_file=source_file,
                page=page,
                content_type=content_type,
                image_path=str(image_path),
                ahash=ahash,
                chunk_index=index,
            )
        )

    if changed:
        cache_path.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return chunks
