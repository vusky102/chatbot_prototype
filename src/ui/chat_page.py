from __future__ import annotations

import base64
import html
import json
import time
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from src.rag import RAGService
from src.tts import TextToSpeechRouter


CARD_WIDTH = 200
CARD_GAP = 12


@st.cache_resource
def _get_tts() -> TextToSpeechRouter:
    """Cached TTS router shared across Streamlit reruns."""
    return TextToSpeechRouter()


def _ensure_tts_state() -> None:
    """Initialize session keys used for mp3 path caching."""
    st.session_state.setdefault("tts_cache", {})


def _synthesize_cached(text: str, cache_key: str) -> Path:
    """Return a cached mp3 path for this bubble, synthesizing if needed."""
    _ensure_tts_state()
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("Nothing to play.")

    cache: dict = st.session_state.tts_cache
    cached = Path(cache.get(cache_key) or "")
    if cached.is_file():
        return cached

    path = Path(_get_tts().synthesize(cleaned))
    cache[cache_key] = str(path)
    return path


def _play_mp3_in_browser(path: Path, cache_key: str) -> None:
    """Register mp3 in page JS cache and autoplay (nonce forces remount each time)."""
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    key_js = json.dumps(cache_key)
    payload_js = json.dumps(payload)
    nonce = time.time_ns()
    st.html(
        f"""
        <script>
        (function() {{
          window.__ttsAudio = window.__ttsAudio || {{}};
          window.__ttsAudio[{key_js}] = {payload_js};
          const audio = new Audio("data:audio/mpeg;base64," + {payload_js});
          audio.play().catch(function() {{}});
        }})();
        </script>
        <!-- tts-play {nonce} -->
        """,
        unsafe_allow_javascript=True,
    )


@st.fragment
def _tts_hidden_button(cache_key: str, text: str) -> None:
    """Hidden Streamlit button triggered by clicking the HTML volume glyph."""
    safe_key = html.escape(cache_key)
    st.markdown(
        f'<div class="tts-btn-marker tts-key-{safe_key}"></div>',
        unsafe_allow_html=True,
    )
    if st.button(
        "Play",
        key=f"tts_btn_{cache_key}",
        type="tertiary",
    ):
        try:
            with st.spinner("Generating speech..."):
                path = _synthesize_cached(text, cache_key)
            _play_mp3_in_browser(path, cache_key)
        except Exception as exc:
            st.caption(f"TTS: {exc}")


def _inject_tts_glyph_bridge() -> None:
    """Wire .tts-glyph clicks → play cached audio or hidden Streamlit button."""
    # st.html (not components.html): JS runs in-page, not in a sandboxed iframe.
    st.html(
        """
        <script>
        (() => {
          const keyFromClass = (el) => {
            const found = [...el.classList].find((c) => c.startsWith("tts-key-"));
            return found ? found.slice("tts-key-".length) : null;
          };

          const findHost = (glyph) => {
            let node = glyph;
            while (node) {
              if (
                node.matches?.('[data-testid="stVerticalBlock"]') &&
                node.querySelector?.(".tts-btn-marker")
              ) {
                return node;
              }
              node = node.parentElement;
            }
            return null;
          };

          const playCached = (key) => {
            const payload = window.__ttsAudio && window.__ttsAudio[key];
            if (!payload) return false;
            const audio = new Audio("data:audio/mpeg;base64," + payload);
            audio.play().catch(function() {});
            return true;
          };

          const clickStreamlitButton = (glyph, key) => {
            const host = findHost(glyph);
            if (!host) return;
            const marker = host.querySelector(".tts-btn-marker.tts-key-" + key);
            const scope =
              marker?.closest('[data-testid="stVerticalBlock"]') || host;
            const button = scope.querySelector("button");
            if (!button) return;
            button.disabled = false;
            button.click();
          };

          const wireGlyph = (glyph) => {
            if (glyph.dataset.ttsWired === "1") return;
            glyph.dataset.ttsWired = "1";
            glyph.style.cursor = "pointer";
            glyph.title = "Play audio";

            const activate = (event) => {
              event.preventDefault();
              event.stopPropagation();
              const key = keyFromClass(glyph);
              if (!key) return;
              // Replay from JS cache inside the user-gesture (works every click).
              if (playCached(key)) return;
              clickStreamlitButton(glyph, key);
            };

            glyph.addEventListener("click", activate);
            glyph.addEventListener("keydown", (event) => {
              if (event.key === "Enter" || event.key === " ") activate(event);
            });
          };

          const scan = () => {
            document.querySelectorAll(".tts-glyph").forEach(wireGlyph);
          };

          scan();
          if (document.documentElement.dataset.ttsBridge !== "1") {
            document.documentElement.dataset.ttsBridge = "1";
            new MutationObserver(scan).observe(document.body, {
              childList: true,
              subtree: true,
            });
          }
        })();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def _render_user_message(content: str, message_id: int) -> None:
    """Render a right-aligned user bubble with TTS glyph."""
    cache_key = f"user_{message_id}"
    safe_key = html.escape(cache_key)
    with st.container():
        st.markdown(
            (
                '<div class="msg-row msg-row-user">'
                '<div class="bubble bubble-user">'
                '<div class="bubble-header">'
                '<span class="bubble-label">You</span>'
                f'<span class="tts-glyph tts-key-{safe_key}" title="Play audio">'
                "volume_up</span>"
                "</div>"
                f"{_as_html_text(content)}"
                "</div>"
                '<div class="avatar avatar-user">person</div>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        _tts_hidden_button(cache_key, content)


def _render_assistant_thinking() -> None:
    """Show the animated 'Thinking...' assistant placeholder."""
    st.markdown(
        (
            '<div class="msg-row msg-row-assistant">'
            '<div class="avatar avatar-assistant">smart_toy</div>'
            '<div class="assistant-stack">'
            '<div class="bubble bubble-assistant">'
            '<div class="bubble-header">'
            '<span class="bubble-label">Assistant</span>'
            "</div>"
            '<div class="typing-row">'
            '<div class="typing-indicator">'
            "<span></span><span></span><span></span>"
            "</div>"
            '<span class="typing-text">Thinking...</span>'
            "</div>"
            "</div>"
            "</div>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def _render_assistant_message(
    content: str,
    sources: list[dict] | None = None,
    message_id: int | None = None,
) -> None:
    """Render an assistant bubble, optional source carousel, and TTS glyph."""
    sources = sources or []
    if message_id is None:
        message_id = _next_message_id()

    sources_html = ""
    if sources:
        style, sources_html = _carousel_html(sources, message_id=message_id)
        st.markdown(style, unsafe_allow_html=True)

    bubble_class = "bubble bubble-assistant"
    if sources:
        bubble_class += " has-sources"

    cache_key = f"assistant_{message_id}"
    safe_key = html.escape(cache_key)
    with st.container():
        st.markdown(
            (
                '<div class="msg-row msg-row-assistant">'
                '<div class="avatar avatar-assistant">smart_toy</div>'
                '<div class="assistant-stack">'
                f'<div class="{bubble_class}">'
                '<div class="bubble-header">'
                '<span class="bubble-label">Assistant</span>'
                f'<span class="tts-glyph tts-key-{safe_key}" title="Play audio">'
                "volume_up</span>"
                "</div>"
                f'<div class="assistant-answer">{_as_html_text(content)}</div>'
                f"{sources_html}"
                "</div>"
                "</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )
        _tts_hidden_button(cache_key, content)

    if sources:
        _render_source_images(sources)

# Injected only on the empty landing screen so the composer is truly
# vertically centered (Streamlit always mounts chat_input in stBottom).
_EMPTY_COMPOSER_CSS = """
<style>
[data-testid="stBottom"],
section.main [data-testid="stBottom"],
[data-testid="stMain"] [data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"],
.stChatFloatingInputContainer {
  background: #f8f9fa !important;
  background-color: #f8f9fa !important;
  border: none !important;
  border-top: none !important;
  box-shadow: none !important;
}
[data-testid="stBottom"],
section.main [data-testid="stBottom"],
[data-testid="stMain"] [data-testid="stBottom"] {
  position: fixed !important;
  /* Anchor top edge near mid-viewport so growth expands downward
     (avoids overlapping the Hello hero). */
  top: 46% !important;
  bottom: auto !important;
  left: var(--chat-main-left, 0px) !important;
  right: 0 !important;
  width: auto !important;
  transform: none !important;
  z-index: 1000 !important;
  padding: 0 !important;
  margin: 0 !important;
}
[data-testid="stBottomBlockContainer"] {
  max-width: 100% !important;
  width: 100% !important;
  margin: 0 !important;
  padding-top: 0.65rem !important;
  padding-bottom: 0.65rem !important;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
  box-sizing: border-box !important;
}
[data-testid="stChatInput"] {
  width: 100% !important;
  max-width: 100% !important;
}
.block-container {
  padding-bottom: 1rem !important;
}
.chat-empty-hero {
  animation: emptyHeroIn 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes emptyHeroIn {
  from { opacity: 0; transform: translateY(calc(-100% + 12px)); }
  to { opacity: 1; transform: translateY(-100%); }
}
</style>
"""

# Plays once when the first question docks the composer to the bottom.
_DOCK_COMPOSER_CSS = """
<style>
[data-testid="stBottom"],
section.main [data-testid="stBottom"],
[data-testid="stMain"] [data-testid="stBottom"] {
  position: fixed !important;
  left: var(--chat-main-left, 0px) !important;
  right: 0 !important;
  width: auto !important;
  bottom: auto !important;
  z-index: 1000 !important;
  padding: 0 !important;
  margin: 0 !important;
  background: #f8f9fa !important;
  border-top: 1px solid transparent !important;
  animation: dockComposer 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"],
.stChatFloatingInputContainer {
  background: #f8f9fa !important;
}
.chat-empty-hero.is-docking {
  animation: emptyHeroOut 0.35s ease forwards;
}
.msg-row {
  animation: msgArrive 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}
@keyframes dockComposer {
  0% {
    top: 46%;
    transform: none;
    border-top-color: transparent;
  }
  100% {
    top: 100%;
    transform: translateY(-100%);
    border-top-color: #dadce0;
  }
}
@keyframes emptyHeroOut {
  from { opacity: 1; transform: translateY(-100%); }
  to { opacity: 0; transform: translateY(calc(-100% - 16px)); }
}
@keyframes msgArrive {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
"""


def _inject_chat_input_autogrow() -> None:
    """Grow composer with content; keep left inset aligned to the real sidebar."""
    components.html(
        """
<script>
(() => {
  const doc = window.parent.document;
  const win = window.parent;
  const LINE = 24;
  const PAD = 17.6;
  const MIN = LINE + PAD;
  const MAX = MIN * 3;

  function syncMainLeft() {
    const sidebar = doc.querySelector('[data-testid="stSidebar"]');
    let left = 0;
    if (sidebar) {
      const rect = sidebar.getBoundingClientRect();
      if (rect.width > 8 && rect.right > 8) {
        left = Math.round(rect.right);
      }
    }
    doc.documentElement.style.setProperty("--chat-main-left", left + "px");
    return left;
  }

  function pinHero() {
    syncMainLeft();
    const bottom = doc.querySelector('[data-testid="stBottom"]');
    const hero = doc.querySelector(".chat-empty-hero");
    if (!bottom || !hero) return;
    const rect = bottom.getBoundingClientRect();
    hero.style.top = Math.max(rect.top, 0) + "px";
    hero.style.left = rect.left + "px";
    hero.style.width = rect.width + "px";
    hero.style.right = "auto";
    hero.style.transform = "translateY(-100%)";
  }

  function fit(ta) {
    if (!ta) return;
    ta.style.height = MIN + "px";
    ta.style.overflowY = "hidden";
    const needed = ta.scrollHeight;
    const next = Math.min(Math.max(needed, MIN), MAX);
    ta.style.height = next + "px";
    if (needed > MAX + 1) {
      ta.style.overflowY = "scroll";
    } else {
      ta.style.overflowY = "hidden";
    }
    pinHero();
  }

  function bind(ta) {
    if (!ta || ta.dataset.autogrowBound === "1") return;
    ta.dataset.autogrowBound = "1";
    ta.addEventListener("input", () => fit(ta));
    ta.addEventListener("change", () => fit(ta));
    fit(ta);
  }

  function scan() {
    syncMainLeft();
    doc.querySelectorAll('[data-testid="stChatInput"] textarea').forEach(bind);
    pinHero();
  }

  scan();
  win.addEventListener("resize", scan);
  new MutationObserver(scan).observe(doc.body, { childList: true, subtree: true });
})();
</script>
        """,
        height=0,
        width=0,
    )


def _history_for_rag(messages: list[dict]) -> list[dict[str, str]]:
    """Build chat history for RAG, excluding the latest user turn."""
    history: list[dict[str, str]] = []
    for message in messages:
        if message["role"] in {"user", "assistant"} and message.get("content"):
            history.append(
                {"role": message["role"], "content": str(message["content"])}
            )
    return history[:-1]


def _as_html_text(text: str) -> str:
    """Escape text and preserve line breaks for bubble HTML."""
    return html.escape(text).replace("\n", "<br>")


def _next_message_id() -> int:
    """Allocate a monotonic message id for the current session."""
    current = int(st.session_state.get("msg_seq", 0)) + 1
    st.session_state.msg_seq = current
    return current


def _format_pages(pages: list[int]) -> str:
    """Human-readable page list for source cards (Vietnamese labels)."""
    if not pages:
        return "trang ?"
    if len(pages) == 1:
        return f"trang {pages[0]}"
    return "trang " + ", ".join(str(page) for page in pages)


def _group_sources_by_file(sources: list[dict]) -> list[dict]:
    """UI-only: one card per file, pages listed together."""
    grouped: dict[str, dict] = {}
    order: list[str] = []

    for source in sources:
        key = str(source.get("source_file") or "unknown")
        page = int(source.get("page", 0) or 0)
        score = float(source.get("score", 0) or 0)
        content_type = str(source.get("content_type") or "text")
        heading = str(source.get("heading") or "").strip()
        image_path = str(source.get("image_path") or "")

        if key not in grouped:
            order.append(key)
            grouped[key] = {
                "source_file": key,
                "pages": [],
                "score": score,
                "content_types": [],
                "headings": [],
                "image_paths": [],
            }

        item = grouped[key]
        if page and page not in item["pages"]:
            item["pages"].append(page)
        item["score"] = max(float(item["score"]), score)
        if content_type and content_type not in item["content_types"]:
            item["content_types"].append(content_type)
        if heading and heading not in item["headings"]:
            item["headings"].append(heading)
        if image_path and image_path not in item["image_paths"]:
            item["image_paths"].append(image_path)

    cards: list[dict] = []
    for key in order:
        item = grouped[key]
        pages = sorted(int(page) for page in item["pages"])
        types = list(item["content_types"])
        headings = list(item["headings"])
        cards.append(
            {
                "source_file": item["source_file"],
                "pages": pages,
                "page_label": _format_pages(pages),
                "score": float(item["score"]),
                "content_type": types[0] if len(types) == 1 else "mixed",
                "heading": headings[0] if len(headings) == 1 else "",
                "hit_count": len(pages) or 1,
                "image_paths": list(item["image_paths"]),
            }
        )
    return cards


def _source_card_html(source: dict) -> str:
    """Build one compact HTML source card for the in-bubble carousel."""
    heading = source.get("heading") or ""
    heading_bit = (
        f'<div class="source-mini-heading">{html.escape(str(heading))}</div>'
        if heading
        else ""
    )
    hit_count = int(source.get("hit_count", 1) or 1)
    hit_bit = (
        f'<span class="hit-pill">{hit_count} đoạn</span>' if hit_count > 1 else ""
    )
    page_label = source.get("page_label") or _format_pages(
        [int(source.get("page", 0) or 0)]
    )
    return (
        '<div class="source-mini-card">'
        '<div class="source-mini-top">'
        f'<span class="type-pill">{html.escape(str(source.get("content_type", "text")))}</span>'
        f"{hit_bit}"
        f'<span class="score-pill">{float(source.get("score", 0)):.2f}</span>'
        "</div>"
        f'<div class="source-mini-file">'
        f'{html.escape(str(source.get("source_file", "unknown")))}'
        "</div>"
        f'<div class="source-mini-meta">{html.escape(str(page_label))}</div>'
        f"{heading_bit}"
        "</div>"
    )


def _carousel_html(sources: list[dict], message_id: int) -> tuple[str, str]:
    """Return (style_tag, carousel_html) with ‹ › as in-bubble HTML labels.

    Streamlit widgets cannot nest inside markdown HTML, so navigation uses
    radio + label (CSS only) instead of st.button overlays.
    Cards are grouped by file for display only.
    """
    cards = _group_sources_by_file(sources)
    total = len(cards)
    group = f"src{message_id}"
    step = CARD_WIDTH + CARD_GAP

    radios = "".join(
        (
            f'<input class="src-radio" type="radio" name="{group}" '
            f'id="{group}-{i}"{" checked" if i == 0 else ""}>'
        )
        for i in range(total)
    )
    counts = "".join(
        f'<span class="src-count src-count-{i}">{i + 1}/{total}</span>'
        for i in range(total)
    )
    cards_html = "".join(_source_card_html(card) for card in cards)

    if total <= 1:
        nav_html = ""
    else:
        nav_sets = []
        for i in range(total):
            prev_i = (i - 1) % total
            next_i = (i + 1) % total
            nav_sets.append(
                f'<div class="src-nav-set src-nav-{i}">'
                f'<label class="src-nav-btn" for="{group}-{prev_i}">‹</label>'
                f'<label class="src-nav-btn" for="{group}-{next_i}">›</label>'
                f"</div>"
            )
        nav_html = f'<div class="src-nav-row">{"".join(nav_sets)}</div>'

    rules: list[str] = []
    for i in range(total):
        offset = i * step
        rules.append(
            f"#{group}-{i}:checked ~ .source-carousel-frame .source-carousel-track"
            f"{{transform:translateX(-{offset}px);}}"
        )
        rules.append(
            f"#{group}-{i}:checked ~ .source-section-title .src-count-{i}"
            f"{{display:inline-flex;}}"
        )
        rules.append(
            f"#{group}-{i}:checked ~ .source-carousel-frame "
            f".source-mini-card:nth-child({i + 1}){{"
            f"background:var(--md-sys-color-primary-container);"
            f"border-color:transparent;box-shadow:var(--md-elevation-2);}}"
        )
        rules.append(
            f"#{group}-{i}:checked ~ .source-carousel-frame "
            f".source-mini-card:nth-child({i + 1}) .type-pill{{"
            f"background:rgba(11,87,208,.12);color:var(--md-sys-color-primary);}}"
        )
        rules.append(
            f"#{group}-{i}:checked ~ .source-carousel-frame "
            f".source-mini-card:nth-child({i + 1}) .score-pill{{"
            f"background:var(--md-sys-color-primary);}}"
        )
        if total > 1:
            rules.append(
                f"#{group}-{i}:checked ~ .src-nav-row .src-nav-{i}"
                f"{{display:flex;}}"
            )

    style = f"<style>{''.join(rules)}</style>"
    body = (
        f'<div class="source-carousel">'
        f"{radios}"
        f'<div class="source-section-title">'
        f"Nguồn tham chiếu"
        f'<span class="source-count-inline">{counts}</span>'
        f"</div>"
        f'<div class="source-carousel-frame">'
        f'<div class="source-carousel-track">{cards_html}</div>'
        f"</div>"
        f"{nav_html}"
        f"</div>"
    )
    return style, body


def _render_source_images(sources: list[dict]) -> None:
    """Show expandable previews for retrieved visual assets."""
    seen: set[str] = set()
    for source in sources:
        image_path = str(source.get("image_path") or "")
        if not image_path or image_path in seen:
            continue
        path = Path(image_path)
        if not path.is_file():
            continue
        seen.add(image_path)
        label = (
            f"Ảnh · {source.get('source_file', path.name)} · "
            f"trang {int(source.get('page', 0) or 0)}"
        )
        with st.expander(label, expanded=False):
            st.image(str(path), use_container_width=True)


def render_chat_page(service: RAGService) -> None:
    """Chat UI: message history, composer, thinking state, and RAG answers."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "msg_seq" not in st.session_state:
        st.session_state.msg_seq = 0
    _ensure_tts_state()

    is_empty = (
        not st.session_state.messages
        and not st.session_state.get("pending_question")
    )

    if is_empty:
        st.markdown('<div class="chat-page-marker chat-empty-state"></div>', unsafe_allow_html=True)
        st.markdown(_EMPTY_COMPOSER_CSS, unsafe_allow_html=True)
        st.markdown(
            (
                '<div class="chat-empty-hero">'
                '<div class="chat-empty-title">Hello</div>'
                "</div>"
            ),
            unsafe_allow_html=True,
        )
    else:
        dock = bool(st.session_state.pop("dock_composer_animation", False))
        marker = "chat-docking-state" if dock else "chat-active-state"
        st.markdown(
            f'<div class="chat-page-marker {marker}"></div>',
            unsafe_allow_html=True,
        )
        if dock:
            st.markdown(_DOCK_COMPOSER_CSS, unsafe_allow_html=True)
            st.markdown(
                (
                    '<div class="chat-empty-hero is-docking">'
                    '<div class="chat-empty-title">Hello</div>'
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        for index, message in enumerate(st.session_state.messages):
            if message["role"] == "user":
                user_id = int(message.get("id") or (index + 1))
                _render_user_message(str(message["content"]), message_id=user_id)
            else:
                _render_assistant_message(
                    str(message["content"]),
                    sources=list(message.get("sources") or []),
                    message_id=int(message.get("id") or (index + 1)),
                )
        _inject_tts_glyph_bridge()

    pending = st.session_state.get("pending_question")
    thinking_slot = st.empty()
    if pending:
        with thinking_slot.container():
            _render_assistant_thinking()

    # Last main-body widget → Streamlit bottom bar (centered when empty via CSS).
    prompt = st.chat_input("Ask a question...")
    _inject_chat_input_autogrow()
    if prompt:
        starting_fresh = not st.session_state.messages
        user_id = _next_message_id()
        st.session_state.messages.append(
            {"role": "user", "content": prompt, "id": user_id}
        )
        st.session_state.pending_question = prompt
        if starting_fresh:
            st.session_state.dock_composer_animation = True
        st.rerun()

    if not pending:
        return

    try:
        history = _history_for_rag(st.session_state.messages)
        result = service.answer(pending, history=history)
        answer = str(result.get("answer") or "")
        sources = list(result.get("sources") or [])
    except Exception as exc:
        answer = (
            "Xin lỗi, hệ thống tạm thời không trả lời được. "
            f"Chi tiết: {exc}"
        )
        sources = []

    message_id = _next_message_id()
    with thinking_slot.container():
        _render_assistant_message(answer, sources=sources, message_id=message_id)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer,
            "sources": sources,
            "id": message_id,
        }
    )
    st.session_state.pop("pending_question", None)
    st.rerun()
