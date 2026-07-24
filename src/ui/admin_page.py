from __future__ import annotations

import html
import tempfile
import sys
from contextlib import redirect_stdout
from pathlib import Path

import streamlit as st

from src.config import Settings
from src.ingest.pipeline import ingest_pdf
from src.rag import RAGService
from src.ui.rag_session import clear_rag_service_cache
from src.ui.tuning import (
    get_effective_settings,
    init_tuning_state,
    tuning_from_settings,
    validate_tuning,
)
from src.utils.image_resolver import resolve_image_path
from src.ingest.batch_pipeline import create_batch_job, list_batch_jobs, finalize_batch_job


def _load_documents(service: RAGService) -> tuple[list[str], str | None, dict[str, object]]:
    """Load indexed source files and stats; return (files, error, stats)."""
    try:
        stats = service.stats()
        return list(stats.get("source_files") or []), None, stats
    except Exception as exc:
        return [], str(exc), {}


class StreamlitStdoutCapture:
    """Captures stdout text and renders it into a Streamlit container."""

    def __init__(self, placeholder) -> None:
        self.placeholder = placeholder
        self.buffer = ""

    def write(self, text: str) -> None:
        if not text:
            return
        self.buffer += text
        
        if len(self.buffer) > 30000:
            self.buffer = "...\n" + self.buffer[-29900:]
            
        safe_html = html.escape(self.buffer)
        html_code = f'''<style>
#terminal-output-box, #terminal-output-box * {{
    color: #c9d1d9 !important;
    -webkit-text-fill-color: #c9d1d9 !important;
}}
</style>
<div id="terminal-output-box" class="terminal-output" style="
    background-color: #0d1117; 
    font-family: Consolas, 'Courier New', monospace; 
    font-size: 13px; 
    padding: 16px; 
    border-radius: 8px; 
    height: 350px; 
    overflow-y: auto;
    white-space: pre-wrap;
    border: 1px solid #30363d;
    margin-top: 16px;
    margin-bottom: 24px;
    display: flex;
    flex-direction: column-reverse;
"><div style="margin-bottom: auto;">{safe_html}</div></div>'''
        self.placeholder.markdown(html_code, unsafe_allow_html=True)

    def flush(self) -> None:
        pass



def _refresh_documents(service: RAGService) -> None:
    """Refresh Admin document list state from the vector store."""
    documents, error, stats = _load_documents(service)
    st.session_state.admin_documents = documents
    st.session_state.admin_documents_error = error
    st.session_state.admin_documents_stats = stats


def _render_tuning_tab(base_settings: Settings) -> None:
    """Admin tab: edit chunking / retrieval / visual provider overrides."""
    init_tuning_state(base_settings)
    tuning = dict(st.session_state.rag_tuning)

    st.subheader("Chunking")
    col_size, col_overlap = st.columns(2)
    with col_size:
        tuning["chunk_size"] = st.number_input(
            "Chunk size",
            min_value=100,
            max_value=4000,
            value=int(tuning["chunk_size"]),
            step=50,
            help="Characters per chunk when using fixed/heading strategies.",
        )
    with col_overlap:
        tuning["chunk_overlap"] = st.number_input(
            "Chunk overlap",
            min_value=0,
            max_value=500,
            value=int(tuning["chunk_overlap"]),
            step=10,
            help="Overlap between consecutive chunks.",
        )

    from src.ingest.chunking import CHUNK_STRATEGIES

    tuning["chunk_strategy"] = st.selectbox(
        "Chunk strategy",
        options=list(CHUNK_STRATEGIES),
        index=list(CHUNK_STRATEGIES).index(str(tuning["chunk_strategy"]))
        if str(tuning["chunk_strategy"]) in CHUNK_STRATEGIES
        else 0,
    )

    st.subheader("Retrieval")
    col_top_k, col_threshold = st.columns(2)
    with col_top_k:
        tuning["retrieval_top_k"] = st.number_input(
            "Top K",
            min_value=1,
            max_value=20,
            value=int(tuning["retrieval_top_k"]),
            help="Number of chunks passed to the answer generator.",
        )
    with col_threshold:
        tuning["retrieval_score_threshold"] = st.slider(
            "Score threshold",
            min_value=0.0,
            max_value=1.0,
            value=float(tuning["retrieval_score_threshold"]),
            step=0.05,
            help="Minimum similarity score to keep a retrieved chunk.",
        )

    col_mult, col_dedup = st.columns(2)
    with col_mult:
        tuning["retrieval_candidate_multiplier"] = st.number_input(
            "Candidate multiplier",
            min_value=1,
            max_value=10,
            value=int(tuning["retrieval_candidate_multiplier"]),
            help="Fetch top_k × multiplier candidates before deduplication.",
        )
    with col_dedup:
        tuning["retrieval_dedup_enabled"] = st.toggle(
            "Enable deduplication",
            value=bool(tuning["retrieval_dedup_enabled"]),
        )

    tuning["retrieval_dedup_threshold"] = st.slider(
        "Dedup threshold",
        min_value=0.0,
        max_value=0.5,
        value=float(tuning["retrieval_dedup_threshold"]),
        step=0.01,
        disabled=not bool(tuning["retrieval_dedup_enabled"]),
        help="Minimum cosine distance between kept chunks (higher = stricter).",
    )

    st.subheader("Vector Database")

    _BACKEND_OPTIONS = ["pinecone", "chromadb"]
    _BACKEND_LABELS = {
        "pinecone": "☁️  Pinecone (cloud · hybrid BM25+dense)",
        "chromadb": "💾  ChromaDB (local · dense-only)",
    }
    current_backend = str(tuning.get("vector_db_backend", "auto")).lower()
    # Map "auto" to whatever default index for UI purposes.
    if current_backend not in _BACKEND_OPTIONS:
        current_backend = "pinecone"
    backend_index = _BACKEND_OPTIONS.index(current_backend)

    selected_backend = st.selectbox(
        "Database backend",
        options=_BACKEND_OPTIONS,
        index=backend_index,
        format_func=lambda b: _BACKEND_LABELS.get(b, b),
        help=(
            "**Pinecone**: Cloud-hosted with hybrid BM25+dense search. "
            "Requires a valid API key.\n\n"
            "**ChromaDB**: Local persistent vector DB. Dense semantic search only. "
            "No API key needed."
        ),
    )
    tuning["vector_db_backend"] = selected_backend

    if selected_backend == "chromadb":
        st.info(
            "📦 ChromaDB stores data locally in `./chroma_db/`. "
            "Hybrid BM25 search is not available — retrieval uses dense "
            "semantic matching only.",
            icon="ℹ️",
        )
    else:
        st.caption("Using cloud Pinecone with hybrid BM25+dense retrieval.")

    st.subheader("Visual ingest")
    tuning["visual_provider"] = st.selectbox(
        "Visual provider",
        options=["gemini", "openai"],
        index=0 if str(tuning["visual_provider"]).lower() == "gemini" else 1,
        help="Vision model used when extracting captions from PDF visuals.",
    )

    st.caption(
        "Settings apply to this browser session only. Defaults come from `.env`."
    )

    apply_col, reset_col = st.columns(2)
    with apply_col:
        if st.button("Apply settings", type="primary", width="stretch"):
            error = validate_tuning(tuning)
            if error:
                st.error(error)
            else:
                st.session_state.rag_tuning = tuning
                clear_rag_service_cache()
                # Force document list refresh for new backend.
                st.session_state.pop("admin_documents", None)
                st.session_state.pop("admin_documents_error", None)
                st.session_state.pop("admin_documents_stats", None)
                st.success("Settings applied.")
                st.rerun()
    with reset_col:
        if st.button("Reset to .env defaults", width="stretch"):
            st.session_state.rag_tuning = tuning_from_settings(base_settings)
            clear_rag_service_cache()
            # Force document list refresh.
            st.session_state.pop("admin_documents", None)
            st.session_state.pop("admin_documents_error", None)
            st.session_state.pop("admin_documents_stats", None)
            st.rerun()


def _render_documents(service: RAGService, base_settings: Settings) -> None:
    """Admin tab: upload PDFs, list indexed sources, delete documents."""
    effective = get_effective_settings(base_settings)

    flash = st.session_state.pop("admin_upload_flash", None)
    if flash:
        for line in flash.get("successes", []):
            st.success(f"Indexed {line}")
        for line in flash.get("failures", []):
            st.error(f"Failed {line}")

    delete_flash = st.session_state.pop("admin_delete_flash", None)
    if delete_flash:
        if delete_flash.get("ok"):
            st.success(delete_flash["message"])
        else:
            st.error(delete_flash["message"])

    st.subheader("Upload documents")

    if "admin_uploader_key" not in st.session_state:
        st.session_state.admin_uploader_key = 0

    indexing = bool(st.session_state.get("admin_indexing_active"))
    queue: list[dict[str, object]] = list(
        st.session_state.get("admin_index_queue") or []
    )

    uploaded_files = st.file_uploader(
        "Choose PDFs to add to the knowledge base",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"admin_pdf_uploader_{st.session_state.admin_uploader_key}",
        disabled=indexing,
    )
    include_visuals = st.toggle(
        "Extract visuals (images, tables, charts, diagrams) + aHash",
        value=True,
        disabled=indexing,
    )
    st.caption(
        f"Using chunk strategy `{effective.chunk_strategy}`, "
        f"size `{effective.chunk_size}`, overlap `{effective.chunk_overlap}`. "
        "Change these in the **Settings** tab."
    )

    if indexing and queue:
        total = int(st.session_state.get("admin_index_total") or len(queue))
        done = int(st.session_state.get("admin_index_done") or 0)
        current_name = str(queue[0]["name"])
        st.progress(
            done / total if total else 0.0,
            text=f"Indexing {current_name} ({done + 1}/{total})…",
        )
        chips = "".join(
            (
                '<span class="upload-queue-chip">'
                f'<span class="upload-queue-chip-name">{html.escape(str(item["name"]))}</span>'
                "</span>"
            )
            for item in queue
        )
        st.markdown(
            f'<div class="upload-queue-row">{chips}</div>',
            unsafe_allow_html=True,
        )

        item = queue[0]
        st.markdown(f"**Detailed Logs: {html.escape(str(item['name']))}**")
        log_placeholder = st.empty()
        
        try:
            with tempfile.TemporaryDirectory() as tmp:
                pdf_path = Path(tmp) / str(item["name"])
                pdf_path.write_bytes(bytes(item["data"]))
                
                with redirect_stdout(StreamlitStdoutCapture(log_placeholder)):
                    result = ingest_pdf(
                        pdf_path,
                        settings=effective,
                        include_visuals=bool(
                            st.session_state.get("admin_index_include_visuals")
                        ),
                    )
            st.session_state.admin_index_successes.append(
                f"`{result.get('source_file')}` ({result.get('upserted')} chunks)"
            )
        except Exception as exc:
            st.session_state.admin_index_failures.append(
                f"`{item['name']}`: {exc}"
            )

        st.session_state.admin_index_queue = queue[1:]
        st.session_state.admin_index_done = done + 1

        if not st.session_state.admin_index_queue:
            successes = list(st.session_state.pop("admin_index_successes", []))
            failures = list(st.session_state.pop("admin_index_failures", []))
            st.session_state.admin_indexing_active = False
            st.session_state.pop("admin_index_total", None)
            st.session_state.pop("admin_index_done", None)
            st.session_state.pop("admin_index_include_visuals", None)
            st.session_state.admin_upload_flash = {
                "successes": successes,
                "failures": failures,
            }
            if successes:
                _refresh_documents(service)
            st.rerun()

        st.rerun()

    file_count = len(uploaded_files or [])
    if file_count and not indexing:
        st.caption(f"{file_count} file{'s' if file_count != 1 else ''} selected.")

    if st.button(
        "Upload and index",
        type="primary",
        disabled=not uploaded_files or indexing,
        width="stretch",
    ):
        if not uploaded_files:
            return
        st.session_state.admin_index_queue = [
            {"name": uploaded.name, "data": uploaded.getvalue()}
            for uploaded in uploaded_files
        ]
        st.session_state.admin_index_total = len(uploaded_files)
        st.session_state.admin_index_done = 0
        st.session_state.admin_index_successes = []
        st.session_state.admin_index_failures = []
        st.session_state.admin_index_include_visuals = include_visuals
        st.session_state.admin_indexing_active = True
        # Clear Streamlit uploader chips; remaining work shows in the queue list.
        st.session_state.admin_uploader_key += 1
        st.rerun()

    st.divider()
    st.subheader("Indexed documents")

    toolbar_left, toolbar_right = st.columns([1, 1])
    with toolbar_left:
        if st.button("Refresh list", width="stretch"):
            _refresh_documents(service)
            st.rerun()
    with toolbar_right:
        stats = st.session_state.get("admin_documents_stats") or {}
        vector_count = stats.get("vector_count")
        count_label = (
            f" · {vector_count} vectors"
            if vector_count is not None
            else ""
        )
        # Show backend-aware index info.
        effective = get_effective_settings(base_settings)
        backend = effective.vector_db_backend
        if backend == "chromadb":
            index_label = "💾 ChromaDB · `rag-chatbot`"
        else:
            index_label = (
                f"☁️ Pinecone · `{base_settings.pinecone_index_name}` · "
                f"`{base_settings.pinecone_namespace}`"
            )
        st.caption(f"{index_label}{count_label}")

    error = st.session_state.get("admin_documents_error")
    if error:
        st.error(f"Could not load documents: {error}")

    documents = list(st.session_state.get("admin_documents") or [])

    if not documents:
        st.info("No documents indexed yet. Upload a PDF above to get started.")
        return

    search_query = st.text_input(
        "Search documents by filename",
        placeholder="Filter...",
        key="admin_search_docs",
    )
    
    if search_query:
        documents = [doc for doc in documents if search_query.lower() in doc.lower()]

    def _delete_document(source_name: str) -> None:
        try:
            with st.spinner(f"Deleting {source_name}..."):
                deleted = service.delete_source(source_name)
            st.session_state.admin_delete_flash = {
                "ok": True,
                "message": (
                    f"Deleted `{source_name}` ({deleted} vectors)."
                    if deleted
                    else f"Delete requested for `{source_name}` "
                    "(metadata filter; list may lag briefly)."
                ),
            }
            _refresh_documents(service)
            st.rerun()
        except Exception as exc:
            st.session_state.admin_delete_flash = {
                "ok": False,
                "message": f"Delete failed for `{source_name}`: {exc}",
            }
            st.rerun()

    if not documents:
        st.info("No documents match your search.")
    else:
        items_per_page = 10
        total_pages = max(1, (len(documents) - 1) // items_per_page + 1)
        
        if "admin_docs_page" not in st.session_state:
            st.session_state.admin_docs_page = 1
            
        if st.session_state.admin_docs_page > total_pages:
            st.session_state.admin_docs_page = total_pages
        if st.session_state.admin_docs_page < 1:
            st.session_state.admin_docs_page = 1
            
        start_idx = (st.session_state.admin_docs_page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_docs = documents[start_idx:end_idx]

        for name in paginated_docs:
            safe_name = html.escape(name)
            name_col, action_col = st.columns([1, 0.08], vertical_alignment="center")
            with name_col:
                st.markdown(
                    (
                        '<div class="doc-row">'
                        '<span class="doc-row-icon">description</span>'
                        f'<span class="doc-row-name">{safe_name}</span>'
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )
            with action_col:
                if st.button(
                    "",
                    key=f"del_{name}",
                    help=f"Delete {name}",
                    icon=":material/delete:",
                    type="tertiary",
                ):
                    _delete_document(name)

        # Pagination controls bottom
        if total_pages > 1:
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            curr_page = st.session_state.admin_docs_page
            
            # Window of max 4 clickable page numbers closest to current page
            max_visible = 4
            if total_pages <= max_visible:
                start_p = 1
                end_p = total_pages
            else:
                start_p = max(1, curr_page - 1)
                end_p = start_p + max_visible - 1
                if end_p > total_pages:
                    end_p = total_pages
                    start_p = max(1, end_p - max_visible + 1)

            visible_pages = list(range(start_p, end_p + 1))
            total_cols = 4 + len(visible_pages)
            
            cols = st.columns(total_cols, gap="small")
            col_idx = 0

            # First page: |<
            with cols[col_idx]:
                if st.button("|<", key="p_first", disabled=(curr_page <= 1), width="stretch"):
                    st.session_state.admin_docs_page = 1
                    st.rerun()
            col_idx += 1

            # Previous page: <
            with cols[col_idx]:
                if st.button("<", key="p_prev", disabled=(curr_page <= 1), width="stretch"):
                    st.session_state.admin_docs_page = curr_page - 1
                    st.rerun()
            col_idx += 1

            # Clickable page numbers
            for p in visible_pages:
                with cols[col_idx]:
                    btn_type = "primary" if p == curr_page else "secondary"
                    if st.button(str(p), key=f"p_num_{p}", type=btn_type, width="stretch"):
                        st.session_state.admin_docs_page = p
                        st.rerun()
                col_idx += 1

            # Next page: >
            with cols[col_idx]:
                if st.button(">", key="p_next", disabled=(curr_page >= total_pages), width="stretch"):
                    st.session_state.admin_docs_page = curr_page + 1
                    st.rerun()
            col_idx += 1

            # Last page: >|
            with cols[col_idx]:
                if st.button(">|", key="p_last", disabled=(curr_page >= total_pages), width="stretch"):
                    st.session_state.admin_docs_page = total_pages
                    st.rerun()

            st.markdown(
                f"<div style='text-align: center; color: #8b949e; font-size: 0.85em; margin-top: 8px;'>Page {curr_page} of {total_pages} ({len(documents)} total documents)</div>",
                unsafe_allow_html=True,
            )

    st.divider()
    manual_name = st.text_input(
        "Delete by filename",
        placeholder="Public_035.pdf",
        help="Use when a file is not listed but you know its indexed name.",
    )
    if st.button(
        "Delete filename above",
        disabled=not manual_name.strip(),
        width="stretch",
    ):
        target = manual_name.strip()
        _delete_document(target)


def _render_debug_tab(service: RAGService, settings: Settings) -> None:
    """Admin tab: run a retrieval probe and inspect returned chunks."""
    effective = get_effective_settings(settings)
    st.caption(
        f"Using top_k={effective.retrieval_top_k}, "
        f"threshold={effective.retrieval_score_threshold}, "
        f"dedup={'on' if effective.retrieval_dedup_enabled else 'off'}."
    )

    query_col, btn_col = st.columns([6, 1], gap="small", vertical_alignment="center")
    with query_col:
        query = st.text_input(
            "Test query",
            key="admin_debug_query",
            placeholder="Ask a retrieval question...",
            label_visibility="collapsed",
        )
    with btn_col:
        submitted = st.button(
            "Retrieve",
            type="primary",
            width="stretch",
            key="admin_debug_retrieve_btn",
        )

    if submitted:
        if not str(query or "").strip():
            st.warning("Enter a query first.")
            return
        with st.spinner("Retrieving..."):
            try:
                results = service.retrieve(query.strip())
                st.session_state.admin_debug_results = [
                    {
                        "citation": item.citation,
                        "score": float(item.score),
                        "content_type": item.content_type,
                        "text": item.text,
                        "image_path": item.image_path,
                        "ahash": item.ahash,
                    }
                    for item in results
                ]
                st.session_state.admin_debug_error = None
                st.session_state.admin_debug_query_ran = query.strip()
            except Exception as exc:
                st.session_state.admin_debug_results = []
                st.session_state.admin_debug_error = str(exc)
                st.session_state.admin_debug_query_ran = query.strip()

    error = st.session_state.get("admin_debug_error")
    if error:
        st.error(f"Retrieve failed: {error}")
        return

    results = list(st.session_state.get("admin_debug_results") or [])
    ran_query = st.session_state.get("admin_debug_query_ran")
    if ran_query is None:
        return

    st.caption(f"Results for: `{ran_query}`")
    if not results:
        st.warning(
            "No results. Try a lower score threshold in Settings, "
            "or confirm documents are indexed in this namespace."
        )
        return

    for index, item in enumerate(results, 1):
        with st.expander(
            f"#{index} · {item['citation']} · score={item['score']:.3f} · "
            f"{item['content_type']}",
            expanded=index == 1,
        ):
            st.write(item["text"])
            image_path = item.get("image_path") or ""
            if image_path:
                st.code(image_path)
                settings = get_effective_settings()
                path = resolve_image_path(image_path, settings.visual_output_dir)
                if path:
                    st.image(str(path), width="stretch")
            if item.get("ahash"):
                st.caption(f"aHash: {item['ahash']}")


def _render_batch_tab(service: RAGService, settings: Settings) -> None:
    """Admin tab: batch process PDFs asynchronously using Gemini."""
    st.subheader("Create Batch Job")
    
    effective = get_effective_settings(settings)
    if effective.visual_provider.lower() != "gemini":
        st.warning("Batch Indexing is currently only supported with Gemini visual provider. Please change your settings in the 'Settings' tab.")
        return

    flash = st.session_state.pop("admin_batch_flash", None)
    if flash:
        st.success(flash)
        
    error_flash = st.session_state.pop("admin_batch_error", None)
    if error_flash:
        st.error(error_flash)

    uploaded_files = st.file_uploader(
        "Choose PDFs to process in batch",
        type=["pdf"],
        accept_multiple_files=True,
        key="admin_batch_uploader",
    )

    if st.button("Submit Batch Job", type="primary", disabled=not uploaded_files, width="stretch"):
        with st.spinner("Preparing batch job..."):
            try:
                import tempfile
                with tempfile.TemporaryDirectory() as tmp:
                    paths = []
                    for uploaded in uploaded_files:
                        pdf_path = Path(tmp) / str(uploaded.name)
                        pdf_path.write_bytes(bytes(uploaded.getvalue()))
                        paths.append(pdf_path)
                    
                    res = create_batch_job(paths, effective)
                    st.session_state.admin_batch_flash = f"Job created! ID: {res['local_job_id']}"
                    st.rerun()
            except Exception as exc:
                st.session_state.admin_batch_error = f"Failed to submit: {exc}"
                st.rerun()

    st.divider()
    
    st.subheader("Active Batch Jobs")
    if st.button("Refresh Statuses", width="stretch"):
        st.rerun()
        
    jobs = list_batch_jobs()
    if not jobs:
        st.info("No active batch jobs.")
    else:
        for job in jobs:
            local_id = job.get("local_job_id", "unknown")
            gemini_id = job.get("gemini_job_id") or "N/A"
            status = job.get("status", "UNKNOWN")
            vis_count = job.get("visual_count", 0)
            
            with st.container(border=True):
                st.markdown(f"**Job ID:** `{local_id}`")
                st.markdown(f"**Files:** {', '.join(job.get('source_files', []))}")
                col1, col2 = st.columns([3, 1], vertical_alignment="center")
                with col1:
                    if status == "SUCCEEDED":
                        st.success("Status: SUCCEEDED")
                    elif status == "FAILED" or "FAILED" in status:
                        st.error(f"Status: {status} | Error: {job.get('error', '')}")
                    else:
                        st.info(f"Status: {status} | Gemini ID: {gemini_id} | Visuals: {vis_count}")
                        
                with col2:
                    if status == "SUCCEEDED":
                        if st.button("Finalize & Index", key=f"fin_{local_id}", type="primary", width="stretch"):
                            with st.spinner("Downloading results and indexing to Vector DB..."):
                                try:
                                    res = finalize_batch_job(local_id, effective)
                                    st.session_state.admin_batch_flash = f"Successfully indexed {res['upserted']} chunks!"
                                    st.rerun()
                                except Exception as exc:
                                    import logging
                                    logging.getLogger(__name__).error("Failed to finalize batch job", exc_info=True)
                                    st.error(f"Failed to finalize: {exc}")


def _render_usage_dashboard() -> None:
    """Admin tab: usage statistics, session costs, and historical tracking."""
    st.subheader("Usage & Cost Dashboard")
    
    from src.utils.token_tracker import TokenTracker
    from src.utils.budget import get_budget, set_budget, check_budget
    tracker = TokenTracker()
    
    # Budget Config
    st.markdown("### 💸 Budget Configuration")
    with st.container(border=True):
        col1, col2 = st.columns([1, 1], vertical_alignment="bottom")
        current_budget = get_budget()
        with col1:
            new_budget = st.number_input("Cost Threshold ($)", min_value=0.0, step=0.5, value=current_budget, help="Set a budget alert limit for session tracking.")
        with col2:
            if st.button("Save Budget", type="primary"):
                set_budget(new_budget)
                st.success("Budget updated!")
                st.rerun()
                
    st.divider()

    # Session & History Summary
    totals = tracker.get_session_totals()
    history_totals = tracker.get_history_totals()
    
    st.markdown("### 📊 Current Session Summary")
    if check_budget(totals['total_cost']):
        st.error(f"⚠️ Warning: Session cost (${totals['total_cost']:.4f}) has exceeded your budget (${get_budget():.2f})!")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'''<div class="usage-dashboard-card">
        <div class="usage-dashboard-label">API Calls</div>
        <div class="usage-dashboard-val">{totals['num_calls']}</div>
        </div>''', unsafe_allow_html=True)
    with col2:
        st.markdown(f'''<div class="usage-dashboard-card">
        <div class="usage-dashboard-label">Input Tokens</div>
        <div class="usage-dashboard-val">{totals['total_input']:,}</div>
        </div>''', unsafe_allow_html=True)
    with col3:
        st.markdown(f'''<div class="usage-dashboard-card">
        <div class="usage-dashboard-label">Output Tokens</div>
        <div class="usage-dashboard-val">{totals['total_output']:,}</div>
        </div>''', unsafe_allow_html=True)
    with col4:
        st.markdown(f'''<div class="usage-dashboard-card">
        <div class="usage-dashboard-label">Total Cost</div>
        <div class="usage-dashboard-val" style="color: #10b981;">${totals['total_cost']:.4f}</div>
        </div>''', unsafe_allow_html=True)

    st.markdown("<br>### 🌐 All-Time History Summary", unsafe_allow_html=True)
    h_col1, h_col2, h_col3, h_col4 = st.columns(4)
    with h_col1:
        st.markdown(f'''<div class="usage-dashboard-card">
        <div class="usage-dashboard-label">Total API Calls</div>
        <div class="usage-dashboard-val">{history_totals['num_calls']}</div>
        </div>''', unsafe_allow_html=True)
    with h_col2:
        st.markdown(f'''<div class="usage-dashboard-card">
        <div class="usage-dashboard-label">Total Input Tokens</div>
        <div class="usage-dashboard-val">{history_totals['total_input']:,}</div>
        </div>''', unsafe_allow_html=True)
    with h_col3:
        st.markdown(f'''<div class="usage-dashboard-card">
        <div class="usage-dashboard-label">Total Output Tokens</div>
        <div class="usage-dashboard-val">{history_totals['total_output']:,}</div>
        </div>''', unsafe_allow_html=True)
    with h_col4:
        st.markdown(f'''<div class="usage-dashboard-card">
        <div class="usage-dashboard-label">All-Time Cost</div>
        <div class="usage-dashboard-val" style="color: #6366f1;">${history_totals['total_cost']:.4f}</div>
        </div>''', unsafe_allow_html=True)

    # Model Breakdown
    st.markdown("<br>#### Breakdown by Model", unsafe_allow_html=True)
    tab_session_bd, tab_history_bd = st.tabs(["⚡ Current Session", "🌐 All-Time History"])
    
    with tab_session_bd:
        breakdown = tracker.get_breakdown_by_model()
        if not breakdown:
            st.info("No API usage recorded in this session yet.")
        else:
            st.dataframe(breakdown, width="stretch", hide_index=True)
            
    with tab_history_bd:
        history_breakdown = tracker.get_history_breakdown_by_model()
        if not history_breakdown:
            st.info("No historical API usage recorded yet.")
        else:
            st.dataframe(history_breakdown, width="stretch", hide_index=True)
        
    if st.button("Reset Session Counters", type="secondary"):
        tracker.reset_session()
        st.rerun()

    st.divider()
    
    # Persistent History
    st.markdown("### 🕰️ Historical Usage Log")
    st.caption("Logs all past interactions across sessions.")
    history = tracker.get_all_history()
    
    if not history:
        st.info("No historical logs found.")
    else:
        import pandas as pd
        df = pd.DataFrame([vars(r) for r in history])
        df = df.rename(columns={"timestamp": "Time", "model": "Model", "provider": "Provider", "operation": "Operation", "input_tokens": "Input", "output_tokens": "Output", "estimated_cost": "Cost ($)"})
        st.dataframe(df, width="stretch", hide_index=True)
        
        col_export, col_clear = st.columns([1, 1])
        with col_export:
            st.download_button("Export as CSV", tracker.export_csv(), "usage_log.csv", "text/csv")
        with col_clear:
            if st.button("Clear History Log", type="primary"):
                tracker.clear_history()
                st.rerun()

def _render_eval_tab(service: RAGService, settings: Settings) -> None:
    """Admin tab: evaluate the model accuracy on test dataset."""
    st.subheader("Model Evaluation")
    
    from src.eval.eval_runner import EvalRunner
    
    runner = EvalRunner(service, settings)
    
    questions_csv = "docs/Training_data_GD4/input/question.csv"
    ground_truth_md = "docs/Training_data_GD4/real_answer.md"
    output_csv = "evaluation_results.csv"
    
    if "eval_questions" not in st.session_state:
        st.session_state.eval_questions = runner.load_questions(questions_csv)
    if "eval_ground_truth" not in st.session_state:
        st.session_state.eval_ground_truth = runner.load_ground_truth(ground_truth_md)
    if "eval_history" not in st.session_state:
        st.session_state.eval_history = runner.get_history(output_csv)
        
    questions = st.session_state.eval_questions
    ground_truth = st.session_state.eval_ground_truth
    
    total_q = len(questions)
    
    if total_q == 0:
        st.warning(f"Could not load questions from {questions_csv}")
        return
        
    st.markdown(f"**Loaded:** {total_q} questions | Ground truth for {len(ground_truth)}")
    
    st.divider()
    
    col_start, col_limit = st.columns(2)
    with col_start:
        start_idx = st.number_input("Start Question", min_value=1, max_value=total_q, value=1)
    with col_limit:
        limit_val = st.number_input("Limit", min_value=1, max_value=total_q, value=total_q)
        
    st.markdown("### Batch Size Control")
    col_batch, col_parallel = st.columns(2)
    with col_batch:
        batch_size = st.slider(
            "Questions per LLM call", 
            min_value=1, 
            max_value=total_q, 
            value=1,
            help="Higher batch size saves tokens but may dilute LLM attention. 1 = safest, most expensive."
        )
    with col_parallel:
        max_workers = st.slider(
            "Concurrent Workers (Parallel)",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of batches to process simultaneously via asyncio."
        )
    
    if st.button("🚀 Run Evaluation", type="primary", width="stretch"):
        progress_bar = st.progress(0, text="Starting evaluation...")
        
        def on_progress(done: int, total: int, msg: str):
            pct = done / total if total > 0 else 0.0
            progress_bar.progress(pct, text=f"Progress: {done}/{total} - {msg}")
            
        results = runner.run(
            questions=questions,
            batch_size=batch_size,
            start=start_idx,
            limit=limit_val,
            on_progress=on_progress,
            max_workers=max_workers
        )
        
        progress_bar.progress(1.0, text="Evaluation complete! Saving results...")
        
        stats = runner.save_results(
            results, 
            ground_truth, 
            questions, 
            output_csv,
            batch_size=batch_size,
            max_workers=max_workers
        )
        st.session_state.eval_last_stats = stats
        st.session_state.eval_history = runner.get_history(output_csv)
        
    if "eval_last_stats" in st.session_state:
        stats = st.session_state.eval_last_stats
        st.markdown('<div class="eval-stat-card" style="padding: 16px; border: 1px solid #30363d; border-radius: 8px; margin-top: 16px;">', unsafe_allow_html=True)
        st.markdown(f"<h1 style='color: #4ade80;'>{stats['accuracy']:.1f}%</h1>", unsafe_allow_html=True)
        st.markdown(f"<p>Accuracy ({stats['correct']}/{stats['total']})</p>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.success(f"Saved column `{stats['column']}` to `{stats['file']}`")

    st.divider()
    st.subheader("Evaluation History")
    
    history = st.session_state.get("eval_history", [])
    if not history:
        st.info("No evaluation history found. Run an evaluation to see results here.")
    else:
        st.dataframe(history, width="stretch", hide_index=True)

def render_admin_page(service: RAGService, settings: Settings) -> None:
    """Admin UI: documents, tuning, and retrieval debug tabs."""
    st.markdown('<div class="admin-page-marker"></div>', unsafe_allow_html=True)

    # Do not re-scan Pinecone on every interaction (breaks Debug retrieve UX).
    if "admin_documents" not in st.session_state:
        _refresh_documents(service)

    tab_docs, tab_batch, tab_settings, tab_debug, tab_usage, tab_eval = st.tabs(
        ["Manage documents", "Batch Indexing", "Settings", "Debug retrieval", "📊 Usage & Cost", "🧪 Evaluation"]
    )

    with tab_docs:
        _render_documents(service, settings)

    with tab_batch:
        _render_batch_tab(service, settings)

    with tab_settings:
        _render_tuning_tab(settings)

    with tab_debug:
        _render_debug_tab(service, settings)
        
    with tab_usage:
        _render_usage_dashboard()
        
    with tab_eval:
        _render_eval_tab(service, settings)
