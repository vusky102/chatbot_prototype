from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.admin_page import render_admin_page
from src.ui.chat_page import render_chat_page
from src.ui.visualize_page import render_visualize_page
from src.ui.rag_session import get_base_settings, get_rag_service
from src.ui.styles import inject_styles
from src.utils.model_scanner import get_available_models


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

        def _nav_to(p: str):
            st.session_state.sidebar_page = p

        def _new_chat():
            st.session_state.messages = []
            st.session_state.pop("pending_question", None)
            st.session_state.pop("dock_composer_animation", None)

        if page == "Chat":
            st.button("New chat", key="nav_new_chat", width="stretch", type="primary", on_click=_new_chat)
            st.button("Admin", key="nav_to_admin", width="stretch", on_click=_nav_to, args=("Admin",))
            st.button("Visualize", key="nav_to_visualize", width="stretch", on_click=_nav_to, args=("Visualize",))

        else:
            st.button("Chat", key="nav_to_chat", width="stretch", on_click=_nav_to, args=("Chat",))
            if page != "Admin":
                st.button("Admin", key="nav_to_admin", width="stretch", on_click=_nav_to, args=("Admin",))
            if page != "Visualize":
                st.button("Visualize", key="nav_to_visualize", width="stretch", on_click=_nav_to, args=("Visualize",))



        st.segmented_control(
            "Theme Mode",
            options=["System", "Light", "Dark"],
            default="System",
            format_func=lambda x: {
                "System": ":material/desktop_windows:",
                "Light": ":material/light_mode:",
                "Dark": ":material/dark_mode:"
            }.get(x, x),
            key="app_theme_control",
            label_visibility="collapsed",
        )

        try:
            base_s = get_base_settings()
            models = get_available_models(
                base_s.openai_api_key, 
                base_s.openai_base_url,
                base_s.gemini_api_key,
                base_s.openrouter_api_key,
                base_s.openrouter_base_url
            )
            
            def _on_model_change():
                if "rag_tuning" in st.session_state and "app_chat_model" in st.session_state:
                    selected = st.session_state.app_chat_model
                    # if we have a tuple, grab the 2nd element (the model id)
                    model_id = selected[1] if isinstance(selected, tuple) else selected
                    st.session_state.rag_tuning["chat_model"] = model_id
            
            # Retrieve currently active model string (e.g. 'gpt-4o-mini')
            current_model_id = st.session_state.get("rag_tuning", {}).get("chat_model") or base_s.chat_model
            
            # Find the corresponding tuple (Provider, ModelID) from the models list
            current_choice = next((x for x in models if x[1] == current_model_id), None)
            if not current_choice and models:
                current_choice = models[0]
                
            st.selectbox(
                "Chat Model",
                options=models,
                format_func=lambda x: f"[{x[0]}] {x[1]}" if isinstance(x, tuple) else x,
                index=models.index(current_choice) if current_choice in models else 0,
                key="app_chat_model",
                on_change=_on_model_change
            )
        except Exception:
            pass

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
    elif page == "Visualize":
        render_visualize_page(service)
    else:
        render_admin_page(service, settings)



if __name__ == "__main__":
    main()
