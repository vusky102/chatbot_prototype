from pathlib import Path


def test_assistant_container_keeps_visible_message_row_marker():
    source = Path("src/ui/chat_page.py").read_text(encoding="utf-8")

    row_start = source.index('with st.container(key=f"assistant_row_')
    hidden_button = source.index("_tts_hidden_button(cache_key, content)", row_start)
    row_renderer = source[row_start:hidden_button]

    assert 'class="msg-row assistant-row-marker"' in row_renderer
