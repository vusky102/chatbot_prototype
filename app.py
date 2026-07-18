from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.admin_page import render_admin_page
from src.ui.chat_page import render_chat_page
from src.ui.rag_session import get_base_settings, get_rag_service
from src.ui.styles import inject_styles


st.set_page_config(
    page_title="Knowledge Assistant",
    page_icon="◇",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()


def main() -> None:
    """Streamlit entry: sidebar nav + Chat / Admin pages."""
    if "sidebar_page" not in st.session_state:
        st.session_state.sidebar_page = "Chat"

    with st.sidebar:
        st.markdown(
            """
            <div class="nav-brand">
              <div class="nav-brand-icon">menu_book</div>
              <div>
                <div class="nav-brand-text">Knowledge Assistant</div>
                <div class="nav-brand-sub">RAG document chat</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        page = st.session_state.sidebar_page

        if page == "Chat":
            if st.button(
                "New chat",
                key="nav_new_chat",
                width="stretch",
                type="primary",
            ):
                st.session_state.messages = []
                st.session_state.pop("pending_question", None)
                st.session_state.pop("dock_composer_animation", None)
                st.rerun()

            if st.button("Admin", key="nav_to_admin", width="stretch"):
                st.session_state.sidebar_page = "Admin"
                st.rerun()
        else:
            if st.button("Chat", key="nav_to_chat", width="stretch"):
                st.session_state.sidebar_page = "Chat"
                st.rerun()

    try:
        settings = get_base_settings()
        service = get_rag_service()
    except Exception as exc:
        st.error(
            "Không khởi tạo được RAG service. Kiểm tra `.env` "
            "(OPENAI / PINECONE)."
        )
        st.code(str(exc))
        return

    if page == "Chat":
        render_chat_page(service)
    else:
        render_admin_page(service, settings)


if __name__ == "__main__":
    main()
