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
            prev_col, page_col, next_col = st.columns([1, 2, 1], vertical_alignment="center")
            with prev_col:
                if st.button("Previous", key="prev_page_bot", disabled=st.session_state.admin_docs_page <= 1, use_container_width=True):
                    st.session_state.admin_docs_page -= 1
                    st.rerun()
            with page_col:
                st.markdown(f"<div style='text-align: center; color: #8b949e; font-size: 0.9em;'>Page {st.session_state.admin_docs_page} of {total_pages}</div>", unsafe_allow_html=True)
            with next_col:
                if st.button("Next", key="next_page_bot", disabled=st.session_state.admin_docs_page >= total_pages, use_container_width=True):
                    st.session_state.admin_docs_page += 1
                    st.rerun()

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
                if Path(image_path).is_file():
                    st.image(image_path, width="stretch")
            if item.get("ahash"):
                st.caption(f"aHash: {item['ahash']}")


def render_admin_page(service: RAGService, settings: Settings) -> None:
    """Admin UI: documents, tuning, and retrieval debug tabs."""
    st.markdown('<div class="admin-page-marker"></div>', unsafe_allow_html=True)

    # Do not re-scan Pinecone on every interaction (breaks Debug retrieve UX).
    if "admin_documents" not in st.session_state:
        _refresh_documents(service)

    tab_docs, tab_settings, tab_debug = st.tabs(
        ["Manage documents", "Settings", "Debug retrieval"]
    )

    with tab_docs:
        _render_documents(service, settings)

    with tab_settings:
        _render_tuning_tab(settings)

    with tab_debug:
        _render_debug_tab(service, settings)
