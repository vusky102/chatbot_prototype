import json
import uuid
import re
from pathlib import Path
from dataclasses import asdict

from src.config import Settings
from src.ingest.batch_caption import BatchCaptioner
from src.ingest.chunking import chunk_extracted_text, page_text_map
from src.ingest.image_extraction import extract_images
from src.ingest.pdf_text_extraction import extract_text_from_pdf
from src.ingest.visual_caption import (
    CAPTION_PROMPT,
    PAGE_CONTEXT_CHARS,
    _build_visual_text,
    _image_metadata,
    _visual_id,
)
from src.ingest.ahash import compute_ahash
from src.lc.embeddings import build_embeddings
from src.lc.vectorstore import LangChainVectorStoreAdapter
from src.models import DocumentChunk

BATCH_JOBS_DIR = Path("batch_jobs")


def _get_job_dir(job_id: str) -> Path:
    job_dir = BATCH_JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir


def create_batch_job(pdf_paths: list[Path], settings: Settings) -> dict:
    """
    Extracts text and visuals from a list of PDFs.
    Saves the text chunks and pending visual chunks to a local job directory.
    Submits the visuals to the Gemini Batch API for captioning.
    """
    BATCH_JOBS_DIR.mkdir(exist_ok=True)
    
    # We will aggregate all pending chunks across all files
    all_chunks_data = []
    visual_tasks = []
    
    # We need a unique internal ID for our local tracking, in case Gemini job ID is weird
    local_job_id = str(uuid.uuid4())
    job_dir = _get_job_dir(local_job_id)
    
    source_files = []
    
    for pdf_path in pdf_paths:
        source_files.append(pdf_path.name)
        extracted_text = extract_text_from_pdf(str(pdf_path))
        
        # 1. Text chunks
        text_chunks = chunk_extracted_text(
            extracted_text=extracted_text,
            source_file=pdf_path.name,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            chunk_strategy=settings.chunk_strategy,
        )
        
        # Filter valid text chunks (similar to pipeline.py)
        for chunk in text_chunks:
            if chunk.content_type == "text" and not bool(re.search(r'[a-zA-Z0-9]', chunk.text)):
                continue
            all_chunks_data.append(asdict(chunk))
            
        # 2. Extract images
        try:
            result = extract_images(
                pdf_path=str(pdf_path),
                output_dir=settings.visual_output_dir,
                provider=settings.visual_provider,
            )
            output_dir = result.get("output_dir")
            visual_dir = Path(output_dir) if output_dir else None
            
            if visual_dir and visual_dir.exists():
                page_texts = page_text_map(extracted_text)
                elements_map = {el["filename"]: el for el in (result.get("elements") or [])}
                
                image_paths = sorted(
                    path for path in visual_dir.iterdir()
                    if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
                )
                
                for index, image_path in enumerate(image_paths):
                    page, content_type = _image_metadata(image_path)
                    el_info = elements_map.get(image_path.name)
                    center_x_pct = el_info.get("center_x_pct", 0) if el_info else 0
                    center_y_pct = el_info.get("center_y_pct", 0) if el_info else 0
                    
                    chunk_id = _visual_id(pdf_path.name, page, content_type, center_x_pct, center_y_pct)
                    
                    page_excerpt = ""
                    co_located = page_texts.get(page, "")
                    if co_located:
                        page_excerpt = re.sub(r"\s+", " ", co_located).strip()[:PAGE_CONTEXT_CHARS]
                    
                    try:
                        ahash = compute_ahash(image_path)
                    except Exception:
                        ahash = ""
                        
                    visual_output_dir_base = Path(settings.visual_output_dir)
                    try:
                        rel_path = str(image_path.relative_to(visual_output_dir_base))
                    except ValueError:
                        rel_path = str(image_path)
                        
                    # Save pending chunk info (we will assemble the final text after captioning)
                    pending_chunk = {
                        "id": chunk_id,
                        "text": "", # To be filled
                        "source_file": pdf_path.name,
                        "page": page,
                        "content_type": content_type,
                        "heading": "",
                        "image_path": rel_path,
                        "ahash": ahash,
                        "chunk_index": index,
                        
                        # Extra metadata needed to build final text
                        "_page_excerpt": page_excerpt,
                        "_is_pending_visual": True
                    }
                    
                    all_chunks_data.append(pending_chunk)
                    
                    visual_tasks.append({
                        "id": chunk_id,
                        "path": image_path
                    })
        except Exception as exc:
            print(f"Warning: Failed to extract visuals for {pdf_path.name}: {exc}")
            
    # Save the local chunks data
    chunks_file = job_dir / "chunks.json"
    chunks_file.write_text(json.dumps(all_chunks_data, ensure_ascii=False, indent=2), encoding="utf-8")
    
    # Submit batch job
    if not visual_tasks:
        # No visuals, meaning the job can be "completed" immediately
        info = {
            "local_job_id": local_job_id,
            "gemini_job_id": None,
            "source_files": source_files,
            "status": "SUCCEEDED", # Ready for finalization
            "visual_count": 0
        }
    else:
        try:
            captioner = BatchCaptioner(provider="gemini")
            gemini_job_id = captioner.create_batch_job(visual_tasks, CAPTION_PROMPT)
            info = {
                "local_job_id": local_job_id,
                "gemini_job_id": gemini_job_id,
                "source_files": source_files,
                "status": "PENDING", # Waiting for Gemini
                "visual_count": len(visual_tasks)
            }
        except Exception as exc:
            import traceback
            err_traceback = traceback.format_exc()
            err_msg = str(exc)
            if not err_msg.strip():
                err_msg = type(exc).__name__
            
            print(f"FAILED to submit batch job to Gemini API!\n{err_traceback}")
            
            # Save the full traceback to a log file in the job directory
            (job_dir / "error.log").write_text(err_traceback, encoding="utf-8")
            
            info = {
                "local_job_id": local_job_id,
                "gemini_job_id": None,
                "source_files": source_files,
                "status": f"FAILED_SUBMISSION: {err_msg}",
                "visual_count": len(visual_tasks)
            }
            
    # Save job metadata
    meta_file = job_dir / "meta.json"
    meta_file.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    
    return info


def list_batch_jobs() -> list[dict]:
    """Lists all local batch jobs and updates their status from Gemini API."""
    if not BATCH_JOBS_DIR.exists():
        return []
        
    jobs = []
    captioner = None
    
    for job_dir in BATCH_JOBS_DIR.iterdir():
        if not job_dir.is_dir():
            continue
            
        meta_file = job_dir / "meta.json"
        if not meta_file.exists():
            continue
            
        try:
            info = json.loads(meta_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
            
        if info.get("status") in ["PENDING", "RUNNING"] and info.get("gemini_job_id"):
            # Fetch updated status from Gemini
            if not captioner:
                try:
                    captioner = BatchCaptioner(provider="gemini")
                except Exception:
                    pass
            if captioner:
                try:
                    status_info = captioner.get_job_status(info["gemini_job_id"])
                    info["status"] = status_info["state"]
                    if status_info.get("error"):
                        info["error"] = status_info["error"]
                    
                    # Update saved meta
                    meta_file.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
                except Exception as exc:
                    pass # Keep old status if fetch fails
                    
        jobs.append(info)
        
    # Sort newest first (using modification time of meta.json)
    jobs.sort(key=lambda j: (BATCH_JOBS_DIR / j["local_job_id"] / "meta.json").stat().st_mtime, reverse=True)
    return jobs


def finalize_batch_job(local_job_id: str, settings: Settings) -> dict:
    """
    Downloads results from Gemini, builds final chunks, and upserts to Vector DB.
    Deletes the job directory after successful insertion.
    """
    job_dir = _get_job_dir(local_job_id)
    meta_file = job_dir / "meta.json"
    chunks_file = job_dir / "chunks.json"
    
    if not meta_file.exists() or not chunks_file.exists():
        raise FileNotFoundError(f"Job {local_job_id} data not found.")
        
    info = json.loads(meta_file.read_text(encoding="utf-8"))
    all_chunks_data = json.loads(chunks_file.read_text(encoding="utf-8"))
    
    captions = {}
    gemini_job_id = info.get("gemini_job_id")
    
    if gemini_job_id:
        captioner = BatchCaptioner(provider="gemini")
        # Ensure it's succeeded
        status_info = captioner.get_job_status(gemini_job_id)
        if status_info["state"] != "SUCCEEDED":
            raise ValueError(f"Job is not SUCCEEDED. State: {status_info['state']}")
            
        captions = captioner.fetch_job_results(gemini_job_id)
        
    # Build final DocumentChunks
    final_chunks = []
    for data in all_chunks_data:
        if data.pop("_is_pending_visual", False):
            # It's a visual chunk
            chunk_id = data["id"]
            caption = captions.get(chunk_id, "")
            page_excerpt = data.pop("_page_excerpt", "")
            
            # Reconstruct the text
            text = _build_visual_text(
                content_type=data["content_type"],
                page=data["page"],
                source_file=data["source_file"],
                caption=caption,
                page_excerpt=page_excerpt
            )
            data["text"] = text
            
        final_chunks.append(DocumentChunk(**data))
        
    if not final_chunks:
        raise ValueError("No valid chunks to index.")
        
    # Upsert to Pinecone/Chroma
    embeddings = build_embeddings(settings)
    store = LangChainVectorStoreAdapter(
        settings,
        embeddings,
        create_if_missing=True,
    )
    
    # Delete old sources first
    source_files = set(c.source_file for c in final_chunks)
    for src in source_files:
        store.delete_source(src)
        
    upserted = store.add_chunks(final_chunks)
    
    # Cleanup job dir
    chunks_file.unlink(missing_ok=True)
    meta_file.unlink(missing_ok=True)
    job_dir.rmdir()
    
    return {
        "upserted": upserted,
        "source_files": list(source_files)
    }
