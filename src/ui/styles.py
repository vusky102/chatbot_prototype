APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Material+Symbols+Outlined:opsz,wght,FILL@24,400,0&display=swap');

:root {
  --md-sys-color-primary: #0b57d0;
  --md-sys-color-on-primary: #ffffff;
  --md-sys-color-primary-container: #d3e3fd;
  --md-sys-color-on-primary-container: #041e49;
  --md-sys-color-secondary-container: #e8eaed;
  --md-sys-color-on-secondary-container: #3c4043;
  --md-sys-color-surface: #f8f9fa;
  --md-sys-color-surface-container: #ffffff;
  --md-sys-color-surface-container-high: #f1f3f4;
  --md-sys-color-on-surface: #1f1f1f;
  --md-sys-color-on-surface-variant: #5f6368;
  --md-sys-color-outline: #dadce0;
  --md-sys-color-outline-variant: #e8eaed;
  --md-elevation-1: 0 1px 2px rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15);
  --md-elevation-2: 0 1px 2px rgba(60,64,67,.3), 0 2px 6px 2px rgba(60,64,67,.15);
  --md-radius-md: 16px;
  --chat-ta-line: 1.5rem;
  --chat-ta-pad: 0.55rem;
  --chat-ta-min: calc(var(--chat-ta-line) + (var(--chat-ta-pad) * 2));
  --chat-ta-max: calc(var(--chat-ta-min) * 3);
}

html, body, .stApp, input, textarea {
  font-family: Roboto, "Segoe UI", sans-serif !important;
}

.stApp {
  background: var(--md-sys-color-surface);
}

.block-container {
  padding-top: 1.25rem !important;
  padding-bottom: 6rem !important;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
  max-width: 100% !important;
  width: 100% !important;
}

/* Chat: keep room above the fixed input (active conversation) */
.block-container:has(.chat-page-marker) {
  padding-bottom: 6.5rem !important;
}

.block-container:has(.chat-empty-state) {
  padding-top: 0 !important;
  padding-bottom: 1rem !important;
  min-height: calc(100vh - 2rem);
}

.chat-page-marker {
  display: none;
}

.chat-empty-state,
.chat-active-state,
.chat-docking-state {
  display: none;
}

/* Sit directly above the empty-state composer (top-anchored at 46%) */
.chat-empty-hero {
  position: fixed;
  top: 46%;
  left: var(--chat-main-left, 0px);
  right: 0;
  transform: translateY(-100%);
  z-index: 1001;
  text-align: center;
  max-width: none;
  margin: 0;
  padding: 0 1.5rem 0.7rem;
  box-sizing: border-box;
  pointer-events: none;
}

body:has([data-testid="stSidebarCollapsedControl"]) .chat-empty-hero,
[data-testid="stSidebar"][aria-expanded="false"] ~ section.main .chat-empty-hero {
  left: 0;
}

.chat-empty-title {
  font-size: clamp(1.75rem, 4vw, 2.35rem);
  font-weight: 500;
  letter-spacing: -0.03em;
  color: var(--md-sys-color-on-surface);
  margin: 0 0 0.4rem 0;
}

/* Admin uses the same full-width content measure as chat */
.block-container:has(.admin-page-marker) {
  max-width: 100% !important;
  width: 100% !important;
  padding-top: 1.75rem !important;
  padding-bottom: 3rem !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stTabs"] {
  margin-top: 0.75rem !important;
}

.admin-page-marker {
  display: none;
}

/* Admin main content — readable text on light surfaces */
.block-container:has(.admin-page-marker) {
  color: #202124;
}

.block-container:has(.admin-page-marker) [data-testid="stMarkdownContainer"] :is(p, span, li, h1, h2, h3, h4),
.block-container:has(.admin-page-marker) label,
.block-container:has(.admin-page-marker) [data-baseweb="select"] > div,
.block-container:has(.admin-page-marker) [data-baseweb="input"] input,
.block-container:has(.admin-page-marker) [data-testid="stTextInput"] input,
.block-container:has(.admin-page-marker) div[data-testid="stTabs"] button,
.block-container:has(.admin-page-marker) [data-testid="stFileUploaderDropzoneInstructions"],
.block-container:has(.admin-page-marker) [data-testid="stFileUploaderDropzoneInstructions"] span {
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
  opacity: 1 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stCaptionContainer"],
.block-container:has(.admin-page-marker) .stCaption {
  color: #5f6368 !important;
  -webkit-text-fill-color: #5f6368 !important;
}

/* Inline `code` values in captions (e.g. heading, 800, 150) */
.block-container:has(.admin-page-marker) [data-testid="stCaptionContainer"] code,
.block-container:has(.admin-page-marker) .stCaption code {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  background: #202124 !important;
  border-radius: 4px !important;
  padding: 0.12em 0.4em !important;
  opacity: 1 !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  vertical-align: middle !important;
  line-height: 1.15 !important;
  box-sizing: border-box !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stTabs"] button[aria-selected="true"] {
  color: #0b57d0 !important;
  -webkit-text-fill-color: #0b57d0 !important;
}

/* Admin form inputs — Streamlit 1.32+ custom containers use secondaryBg (dark).
   Force white surface, dark text, single border. */
.block-container:has(.admin-page-marker) :is(
  [data-testid="stNumberInputContainer"],
  [data-testid="stTextInputRootElement"],
  [data-testid="stTextAreaRootElement"]
) {
  background-color: #ffffff !important;
  background: #ffffff !important;
  border: 1px solid #dadce0 !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) :is(
  [data-testid="stNumberInputField"],
  [data-testid="stTextInput"] input,
  [data-testid="stTextArea"] textarea
) {
  background-color: transparent !important;
  background: transparent !important;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
  caret-color: #202124 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stNumberInput"] [data-testid="stNumberInputContainer"] {
  display: flex !important;
  align-items: stretch !important;
  overflow: hidden !important;
  padding: 0 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stNumberInput"] :is(
  [data-testid="stNumberInputStepDown"],
  [data-testid="stNumberInputStepUp"]
) {
  background-color: #ffffff !important;
  border: none !important;
  border-left: 1px solid #dadce0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stNumberInput"] :is(
  [data-testid="stNumberInputStepDown"]:hover:not(:disabled),
  [data-testid="stNumberInputStepUp"]:hover:not(:disabled)
) {
  background-color: #f8f9fa !important;
  color: #202124 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stNumberInput"] :is(
  [data-testid="stNumberInputStepDown"],
  [data-testid="stNumberInputStepUp"]
) svg {
  fill: #202124 !important;
  color: #202124 !important;
}

.block-container:has(.admin-page-marker) :is(
  [data-testid="stSelectbox"],
  [data-testid="stMultiSelect"]
) div:has(> input) {
  background-color: #ffffff !important;
  background: #ffffff !important;
  border: 1px solid #dadce0 !important;
  border-radius: 10px !important;
  box-shadow: none !important;
}

.block-container:has(.admin-page-marker) :is(
  [data-testid="stSelectbox"],
  [data-testid="stMultiSelect"]
) input {
  background-color: transparent !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
  caret-color: #202124 !important;
}

.block-container:has(.admin-page-marker) :is(
  [data-testid="stSelectbox"],
  [data-testid="stMultiSelect"]
) svg {
  fill: #5f6368 !important;
  color: #5f6368 !important;
}

.block-container:has(.admin-page-marker) :is(
  [data-testid="stTextInput"],
  [data-testid="stNumberInput"],
  [data-testid="stTextArea"]
) :is(input, textarea)::placeholder {
  color: #5f6368 !important;
  -webkit-text-fill-color: #5f6368 !important;
  opacity: 1 !important;
}

/* Legacy baseweb widgets (older Streamlit builds) */
.block-container:has(.admin-page-marker) :is(
  [data-testid="stTextInput"],
  [data-testid="stNumberInput"],
  [data-testid="stSelectbox"],
  [data-testid="stMultiSelect"],
  [data-testid="stTextArea"]
) :is(
  [data-baseweb="input"],
  [data-baseweb="select"]
) {
  background-color: #ffffff !important;
  background: #ffffff !important;
  border: 1px solid #dadce0 !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) :is(
  [data-testid="stTextInput"],
  [data-testid="stNumberInput"],
  [data-testid="stSelectbox"],
  [data-testid="stMultiSelect"],
  [data-testid="stTextArea"]
) :is(
  [data-baseweb="input"] input,
  [data-baseweb="select"] > div
) {
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stWidgetLabel"],
.block-container:has(.admin-page-marker) [data-testid="stWidgetLabel"] p {
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) section[data-testid="stFileUploaderDropzone"] {
  background: #ffffff !important;
  border: 1px dashed #dadce0 !important;
}

.block-container:has(.admin-page-marker) section[data-testid="stFileUploaderDropzone"] :is(
  button,
  span,
  small,
  p,
  div
) {
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) section[data-testid="stFileUploaderDropzone"] button {
  background: #ffffff !important;
  border: 1px solid #dadce0 !important;
}

/* Selected upload chips — white surface, dark text (not theme bodyText/black) */
.block-container:has(.admin-page-marker) [data-testid="stFileChips"],
.block-container:has(.admin-page-marker) [data-testid="stFileChip"] {
  background: #ffffff !important;
  background-color: #ffffff !important;
  border: 1px solid #dadce0 !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stFileChip"] :is(
  [data-testid="stFileChipName"],
  span,
  p,
  small,
  div
) {
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
  opacity: 1 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stFileChipDeleteBtn"],
.block-container:has(.admin-page-marker) [data-testid="stFileChipDeleteBtn"] button,
.block-container:has(.admin-page-marker) [data-testid="stFileChip"] button {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  color: #5f6368 !important;
  -webkit-text-fill-color: #5f6368 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stFileChipDeleteBtn"]:hover,
.block-container:has(.admin-page-marker) [data-testid="stFileChipDeleteBtn"] button:hover,
.block-container:has(.admin-page-marker) [data-testid="stFileChip"] button:hover {
  color: #c5221f !important;
  -webkit-text-fill-color: #c5221f !important;
  background: transparent !important;
}

.block-container:has(.admin-page-marker) [data-testid="stFileChip"] svg {
  fill: #5f6368 !important;
  color: #5f6368 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stFileChipDeleteBtn"]:hover svg,
.block-container:has(.admin-page-marker) [data-testid="stFileChip"] button:hover svg {
  fill: #c5221f !important;
  color: #c5221f !important;
}

/* In-progress upload queue — chips shrink as each file finishes */
.upload-queue-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  margin: 0.35rem 0 0.15rem;
}

.upload-queue-chip {
  display: inline-flex;
  align-items: center;
  background: #ffffff;
  border: 1px solid #dadce0;
  border-radius: 10px;
  padding: 0.35rem 0.65rem;
  color: #202124;
  font-size: 0.85rem;
  font-weight: 500;
}

.upload-queue-chip-name {
  color: #202124;
  -webkit-text-fill-color: #202124;
}

/* Debug retrieval expanders — Streamlit header uses dark secondaryBg;
   admin CSS forces dark text, so force a light header for contrast. */
.block-container:has(.admin-page-marker) [data-testid="stExpander"] {
  background: #ffffff !important;
  border: 1px solid #dadce0 !important;
  border-radius: 10px !important;
  overflow: hidden;
}

.block-container:has(.admin-page-marker) [data-testid="stExpander"] details {
  background: #ffffff !important;
}

.block-container:has(.admin-page-marker) [data-testid="stExpander"] summary,
.block-container:has(.admin-page-marker) [data-testid="stExpander"] .streamlit-expanderHeader,
.block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stExpanderDetails"],
.block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stExpanderIcon"] {
  background: #f1f3f4 !important;
  background-color: #f1f3f4 !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stExpander"] summary :is(p, span, div, label),
.block-container:has(.admin-page-marker) [data-testid="stExpander"] .streamlit-expanderHeader :is(p, span, div, label),
.block-container:has(.admin-page-marker) [data-testid="stExpander"] summary svg,
.block-container:has(.admin-page-marker) [data-testid="stExpander"] .streamlit-expanderHeader svg,
.block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] svg {
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
  fill: #202124 !important;
  opacity: 1 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stExpander"] summary,
.block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
  border-bottom: 1px solid #dadce0 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stMarkdownContainer"] :is(p, span, li, h1, h2, h3, h4) {
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

/* Debug retrieval — full-width composer (no st.form inset) */
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) {
  width: 100% !important;
  margin: 0 !important;
  padding: 0 !important;
  gap: 0.5rem !important;
  align-items: center !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) > div {
  padding-left: 0 !important;
  padding-right: 0 !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) [data-testid="stTextInput"] {
  margin-bottom: 0 !important;
  width: 100% !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) [data-testid="stTextInputRootElement"],
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) [data-baseweb="input"] {
  background: #ffffff !important;
  background-color: #ffffff !important;
  border: 1px solid #dadce0 !important;
  border-radius: 10px !important;
  box-shadow: none !important;
  min-height: 2.6rem !important;
  width: 100% !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) [data-testid="stTextInput"] input {
  background: transparent !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
  font-size: 0.95rem !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) [data-testid="stTextInput"] input::placeholder {
  color: #5f6368 !important;
  -webkit-text-fill-color: #5f6368 !important;
  opacity: 1 !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) .stButton > button[kind="primary"],
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(
  [data-testid="stTextInput"]
):not(:has(.doc-row)) .stButton > button[data-testid="stBaseButton-primary"] {
  border-radius: 10px !important;
  min-height: 2.6rem !important;
  background: #0b57d0 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  border: 1px solid #0b57d0 !important;
  box-shadow: none !important;
  font-weight: 500 !important;
  width: 100% !important;
}

/* Dark / colored surfaces — keep light text */
.block-container:has(.admin-page-marker) .stButton > button[kind="primary"],
.block-container:has(.admin-page-marker) .stButton > button[data-testid="stBaseButton-primary"],
.block-container:has(.admin-page-marker) .stButton > button[kind="primary"] :is(span, p, div),
.block-container:has(.admin-page-marker) .stButton > button[data-testid="stBaseButton-primary"] :is(span, p, div) {
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
  opacity: 1 !important;
}

/* Ensure primary buttons keep blue fill (not white-on-white) */
.block-container:has(.admin-page-marker) .stButton > button[kind="primary"],
.block-container:has(.admin-page-marker) .stButton > button[data-testid="stBaseButton-primary"] {
  background: #0b57d0 !important;
  background-color: #0b57d0 !important;
  border: 1px solid #0b57d0 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

.block-container:has(.admin-page-marker) .stButton > button[kind="primary"]:hover,
.block-container:has(.admin-page-marker) .stButton > button[data-testid="stBaseButton-primary"]:hover {
  background: #0842a0 !important;
  background-color: #0842a0 !important;
  border-color: #0842a0 !important;
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

/* Admin toggles — off-state track/thumb must contrast with page bg (#f8f9fa) */
.block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) [data-testid="stWidgetLabel"],
.block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) [data-testid="stWidgetLabel"] p {
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) > * > div:has(> div):not([data-testid="stWidgetLabel"]) {
  background-color: #dadce0 !important;
  border: 1px solid #9aa0a6 !important;
  box-sizing: border-box !important;
}

.block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) > *:not([data-selected]) > div:has(> div):not([data-testid="stWidgetLabel"]) > div {
  background-color: #ffffff !important;
  box-shadow: 0 1px 2px rgba(60, 64, 67, 0.35) !important;
}

.block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) > *[data-selected] > div:has(> div):not([data-testid="stWidgetLabel"]) {
  background-color: #0b57d0 !important;
  border-color: #0b57d0 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) > *[data-selected] > div:has(> div):not([data-testid="stWidgetLabel"]) > div {
  background-color: #ffffff !important;
  box-shadow: 0 1px 2px rgba(60, 64, 67, 0.25) !important;
}

.block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) > *:not([data-selected]):not([data-disabled]):hover > div:has(> div):not([data-testid="stWidgetLabel"]) {
  background-color: #c4c7c5 !important;
}

.block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) > *[data-selected]:not([data-disabled]):hover > div:has(> div):not([data-testid="stWidgetLabel"]) {
  background-color: #0842a0 !important;
  border-color: #0842a0 !important;
}

/* ── Sidebar (Material drawer) ─────────────────────────── */
[data-testid="stSidebar"] {
  background: var(--md-sys-color-surface-container) !important;
  border-right: 1px solid var(--md-sys-color-outline) !important;
}

/* Ensure sidebar inputs are styled correctly in light mode */
[data-testid="stSidebar"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"]) div:has(> input) {
  background-color: #ffffff !important;
  background: #ffffff !important;
  border: 1px solid #dadce0 !important;
  border-radius: 10px !important;
}
[data-testid="stSidebar"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"]) input {
  background-color: transparent !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
  caret-color: #202124 !important;
}
[data-testid="stSidebar"] :is([data-testid="stSelectbox"], [data-testid="stMultiSelect"]) svg {
  fill: #5f6368 !important;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p {
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

[data-testid="stSidebar"] > div:first-child {
  padding-top: 1.25rem;
}

/* Push the theme toggle to the bottom of the sidebar */
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
  display: flex !important;
  flex-direction: column !important;
  height: 100% !important;
  min-height: calc(100vh - 4rem) !important;
}

[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div:has([data-testid="stSegmentedControl"]) {
  margin-top: auto !important;
  padding-bottom: 1rem !important;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.25rem 0.35rem 1rem;
}

.nav-brand-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
  display: grid;
  place-items: center;
  font-variation-settings: "FILL" 1;
  font-family: "Material Symbols Outlined";
  font-size: 22px;
}

.nav-brand-text {
  font-size: 1.05rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  letter-spacing: -0.01em;
}

.nav-brand-sub {
  font-size: 0.78rem;
  color: var(--md-sys-color-on-surface-variant);
  margin-top: 0.1rem;
}

/* ChatGPT-style sidebar menu buttons — same outlined look for all */
[data-testid="stSidebar"] .stButton {
  margin-bottom: 0.35rem;
}

[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] .stButton > button[kind="primary"],
[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
  justify-content: flex-start !important;
  text-align: left !important;
  border-radius: 10px !important;
  font-weight: 500 !important;
  font-size: 0.92rem !important;
  padding: 0.7rem 0.9rem !important;
  min-height: 2.6rem !important;
  box-shadow: none !important;
  background: #ffffff !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
  border: 1px solid #dadce0 !important;
  transition: background .15s ease, border-color .15s ease !important;
}

[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
  background: #f8f9fa !important;
  border-color: #dadce0 !important;
  box-shadow: none !important;
  color: #202124 !important;
  -webkit-text-fill-color: #202124 !important;
}

/* ── Suggestion chips ──────────────────────────────────── */
div[data-testid="stHorizontalBlock"]:has(button[kind="secondary"]) button,
.stButton > button {
  border-radius: 999px !important;
  border: 1px solid var(--md-sys-color-outline) !important;
  background: var(--md-sys-color-surface-container) !important;
  color: var(--md-sys-color-on-surface) !important;
  font-weight: 500 !important;
  font-size: 0.875rem !important;
  box-shadow: none !important;
  transition: background .15s ease, box-shadow .15s ease !important;
}

.stButton > button:hover {
  background: var(--md-sys-color-surface-container-high) !important;
  box-shadow: var(--md-elevation-1) !important;
  border-color: transparent !important;
}

.stButton > button[kind="primary"],
.stButton > button[data-testid="stBaseButton-primary"] {
  background: var(--md-sys-color-primary) !important;
  background-color: var(--md-sys-color-primary) !important;
  color: var(--md-sys-color-on-primary) !important;
  -webkit-text-fill-color: var(--md-sys-color-on-primary) !important;
  border-color: var(--md-sys-color-primary) !important;
}

.stButton > button[kind="primary"]:hover,
.stButton > button[data-testid="stBaseButton-primary"]:hover {
  filter: brightness(1.05);
  color: #ffffff !important;
  -webkit-text-fill-color: #ffffff !important;
}

/* ── Chat bubbles (Google Chat-inspired) ───────────────── */
.msg-row {
  display: flex;
  width: 100%;
  margin: 0.85rem 0;
  gap: 0.65rem;
  align-items: flex-end;
}

.msg-row-user {
  justify-content: flex-end;
}

.msg-row-assistant {
  justify-content: flex-start;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  font-family: "Material Symbols Outlined";
  font-size: 18px;
  font-variation-settings: "FILL" 1;
}

.avatar-user {
  background: var(--md-sys-color-primary);
  color: #fff;
}

.avatar-assistant {
  background: var(--md-sys-color-primary-container);
  color: var(--md-sys-color-primary);
}

.bubble {
  max-width: min(85%, 880px);
  padding: 0.85rem 1.1rem;
  border-radius: 10px;
  line-height: 1.55;
  word-wrap: break-word;
  overflow-wrap: anywhere;
  font-size: 0.95rem;
}

.bubble-user {
  background: #ffffff;
  color: var(--md-sys-color-on-surface);
  border: 1px solid var(--md-sys-color-outline);
  box-shadow: none;
}

.bubble-user .bubble-label {
  color: #5f6368 !important;
}

.bubble-assistant {
  background: #e8f0fe;
  color: #202124 !important;
  border: 1px solid #d2e3fc;
  max-width: 100%;
  box-shadow: var(--md-elevation-1);
}

.bubble-assistant,
.bubble-assistant p,
.bubble-assistant span:not(.bubble-label):not(.type-pill):not(.score-pill) {
  color: #202124 !important;
}

.bubble-assistant.has-sources {
  margin-bottom: 0;
}

.assistant-answer {
  color: #202124 !important;
}

.assistant-stack {
  flex: 1;
  min-width: 0;
}

.source-carousel {
  position: relative;
  margin: 0.85rem 0 0;
  padding: 0.75rem 0 0.15rem;
  background: transparent;
  border: none;
  border-top: 1px solid #c5d7f5;
  border-radius: 0;
  box-shadow: none;
}

.bubble-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  margin: 0;
  color: #5f6368 !important;
  line-height: 1.2;
}

.bubble-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.3rem;
  min-height: 0;
  line-height: 1.2;
}

.tts-glyph {
  font-family: "Material Symbols Outlined";
  font-size: 1rem;
  line-height: 1;
  color: #5f6368;
  flex-shrink: 0;
  user-select: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.15rem;
  height: 1.15rem;
  cursor: pointer;
}

.tts-glyph:hover {
  color: #0b57d0;
}

/* Hide Streamlit TTS buttons; HTML glyph remains the visible control */
.element-container:has(.tts-btn-marker),
div[data-testid="stElementContainer"]:has(.tts-btn-marker) {
  display: none !important;
}

[data-testid="stVerticalBlock"]:has(.tts-btn-marker):not(:has(.msg-row)) {
  position: absolute !important;
  left: -10000px !important;
  top: 0 !important;
  width: 1px !important;
  height: 1px !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  opacity: 0 !important;
}

.typing-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  min-height: 1.5rem;
  color: #3c4043 !important;
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.28rem;
}

.typing-indicator span {
  width: 0.42rem;
  height: 0.42rem;
  border-radius: 50%;
  background: #0b57d0;
  opacity: 0.35;
  animation: typing-bounce 1.1s infinite ease-in-out;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.3s;
}

.typing-text {
  font-size: 0.9rem;
  color: #3c4043 !important;
}

@keyframes typing-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.35; }
  40% { transform: translateY(-3px); opacity: 1; }
}

/* ── Source carousel (inside assistant bubble) ─────────── */
.source-section-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
  font-weight: 500;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #5f6368;
  margin-bottom: 0.65rem;
}

.source-count-inline {
  font-variant-numeric: tabular-nums;
  letter-spacing: 0;
  text-transform: none;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-radius: 999px;
  padding: 0.1rem 0.5rem;
  font-size: 0.72rem;
  font-weight: 500;
}

.source-carousel-frame {
  overflow: hidden;
  padding: 0.1rem 0.15rem 0.35rem;
}

.source-carousel-track {
  display: flex;
  gap: 12px;
  transition: transform 0.3s cubic-bezier(0.2, 0, 0, 1);
  will-change: transform;
}

.src-radio {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  width: 0;
  height: 0;
}

.src-count {
  display: none;
}

.src-nav-row {
  position: relative;
  min-height: 2.25rem;
  margin-top: 0.35rem;
}

.src-nav-set {
  display: none;
  position: absolute;
  inset: 0;
  align-items: center;
  justify-content: space-between;
  pointer-events: none;
}

.src-nav-btn {
  pointer-events: auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.25rem;
  height: 2.25rem;
  border-radius: 999px;
  background: #fff;
  color: #202124;
  border: 1px solid #dadce0;
  box-shadow: var(--md-elevation-2);
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
  user-select: none;
}

.src-nav-btn:hover {
  background: #f8f9fa;
  border-color: #0b57d0;
  color: #0b57d0;
}

.source-mini-card {
  flex: 0 0 200px;
  width: 200px;
  max-width: 200px;
  box-sizing: border-box;
  background: var(--md-sys-color-surface-container-high);
  border: 1px solid var(--md-sys-color-outline);
  border-radius: var(--md-radius-md);
  padding: 0.85rem;
  min-height: 108px;
  transition: border-color .15s ease, box-shadow .15s ease, background .15s ease;
}

.source-mini-top {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.5rem;
  flex-wrap: wrap;
}

.source-mini-file {
  color: var(--md-sys-color-on-surface);
  font-size: 0.875rem;
  font-weight: 500;
  line-height: 1.35;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.source-mini-meta {
  margin-top: 0.25rem;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.78rem;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.source-mini-heading {
  margin-top: 0.4rem;
  color: var(--md-sys-color-on-surface-variant);
  font-size: 0.78rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.score-pill {
  display: inline-flex;
  align-items: center;
  background: var(--md-sys-color-on-surface);
  color: #fff;
  border-radius: 999px;
  padding: 0.12rem 0.5rem;
  font-size: 0.7rem;
  font-weight: 500;
}

.type-pill {
  display: inline-flex;
  align-items: center;
  background: var(--md-sys-color-secondary-container);
  color: var(--md-sys-color-on-secondary-container);
  border-radius: 999px;
  padding: 0.12rem 0.5rem;
  font-size: 0.7rem;
  font-weight: 500;
}

.hit-pill {
  display: inline-flex;
  align-items: center;
  background: #e8f0fe;
  color: #0b57d0;
  border-radius: 999px;
  padding: 0.12rem 0.5rem;
  font-size: 0.7rem;
  font-weight: 500;
}

/* ── Admin document list ───────────────────────────────── */
/* Merge name + trash into one full-width card */
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) {
  background: #ffffff !important;
  border: 1px solid var(--md-sys-color-outline) !important;
  border-radius: 10px !important;
  /* Equal inset on all sides (incl. delete icon on the right) */
  padding: 0.35rem !important;
  margin: 0.12rem 0 !important;
  align-items: center !important;
  gap: 0.35rem !important;
  width: 100% !important;
  min-height: 2.4rem !important;
  box-sizing: border-box !important;
}

/* Tighten vertical gap between Streamlit element wrappers around doc cards */
.block-container:has(.admin-page-marker) div[data-testid="stElementContainer"]:has(.doc-row),
.block-container:has(.admin-page-marker) div[data-testid="stElementContainer"]:has(
  div[data-testid="stHorizontalBlock"]:has(.doc-row)
) {
  margin-bottom: 0 !important;
  margin-top: 0 !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) > div {
  width: auto !important;
  display: flex !important;
  align-items: center !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) > div:first-child {
  flex: 1 1 auto !important;
  min-width: 0 !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) > div:last-child {
  flex: 0 0 auto !important;
  width: auto !important;
  justify-content: center !important;
  padding: 0 !important;
  margin: 0 !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) [data-testid="stMarkdownContainer"],
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) [data-testid="stMarkdownContainer"] p {
  margin: 0 !important;
  padding: 0 !important;
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
}

.doc-row {
  display: flex;
  align-items: center;
  gap: 0.55rem;
  padding: 0 !important;
  background: transparent;
  border: none;
  border-radius: 0;
  min-height: 1.75rem;
  width: 100%;
  box-sizing: border-box;
}

.doc-row-icon {
  font-family: "Material Symbols Outlined";
  font-size: 1.15rem;
  color: var(--md-sys-color-primary);
  font-variation-settings: "FILL" 1;
  line-height: 1;
  display: inline-flex;
  align-items: center;
}

.doc-row-name {
  color: var(--md-sys-color-on-surface);
  font-size: 0.92rem;
  font-weight: 500;
  word-break: break-word;
  flex: 1 1 auto;
  line-height: 1.25;
  display: flex;
  align-items: center;
}

/* Icon-only trash — flat icon, no circle/pill chrome */
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton {
  margin: 0 !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton > button,
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton > button[kind="secondary"],
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton > button[kind="tertiary"],
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton > button[data-testid^="stBaseButton"] {
  min-height: 1.75rem !important;
  min-width: 1.75rem !important;
  width: 1.75rem !important;
  height: 1.75rem !important;
  padding: 0 !important;
  border-radius: 0 !important;
  border: none !important;
  background: transparent !important;
  background-color: transparent !important;
  box-shadow: none !important;
  color: #5f6368 !important;
  -webkit-text-fill-color: #5f6368 !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton > button:hover,
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton > button[kind="secondary"]:hover,
.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton > button[data-testid^="stBaseButton"]:hover {
  background: transparent !important;
  background-color: transparent !important;
  color: #c5221f !important;
  -webkit-text-fill-color: #c5221f !important;
  border: none !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  filter: none !important;
}

.block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) .stButton > button svg {
  fill: currentColor !important;
}

/* Single-line composer by default; grows up to 3x, then scrolls.
   Row flex + align-items:center = vertical only (not horizontal). */
[data-testid="stChatInput"] {
  display: flex !important;
  flex-direction: row !important;
  align-items: center !important;
  justify-content: flex-start !important;
  border-radius: 10px !important;
  margin-bottom: 0 !important;
  padding: 0.2rem 0.35rem !important;
  min-height: var(--chat-ta-min) !important;
  height: auto !important;
  background: #ffffff !important;
  background-color: #ffffff !important;
  border: 1px solid #dadce0 !important;
  box-shadow: none !important;
  overflow: visible !important;
  gap: 0.35rem !important;
}

[data-testid="stChatInput"] > div {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  align-items: stretch !important;
  justify-content: flex-start !important;
}

[data-testid="stChatInputTextArea"],
[data-testid="stChatInput"] [data-baseweb="base-input"],
[data-testid="stChatInput"] [data-baseweb="textarea"] {
  background: transparent !important;
  background-color: transparent !important;
  border: none !important;
  box-shadow: none !important;
  min-height: var(--chat-ta-min) !important;
  height: auto !important;
  max-height: var(--chat-ta-max) !important;
  flex: 1 1 auto !important;
  width: 100% !important;
  text-align: left !important;
}

[data-testid="stChatInput"] textarea,
[data-testid="stChatInputTextArea"] textarea {
  font-size: 0.95rem !important;
  line-height: var(--chat-ta-line) !important;
  min-height: var(--chat-ta-min) !important;
  max-height: var(--chat-ta-max) !important;
  overflow-y: auto !important;
  resize: none !important;
  padding-top: var(--chat-ta-pad) !important;
  padding-bottom: var(--chat-ta-pad) !important;
  padding-right: 0.35rem !important;
  background: transparent !important;
  background-color: transparent !important;
  color: #202124 !important;
  caret-color: #202124 !important;
  border: none !important;
  text-align: left !important;
  field-sizing: content;
  scrollbar-width: thin;
  scrollbar-color: #9aa0a6 #e8eaed;
  scrollbar-gutter: stable;
}

[data-testid="stChatInput"] textarea::placeholder,
[data-testid="stChatInputTextArea"] textarea::placeholder {
  color: #5f6368 !important;
  opacity: 1 !important;
  -webkit-text-fill-color: #5f6368 !important;
}

[data-testid="stChatInput"] textarea::-webkit-input-placeholder,
[data-testid="stChatInputTextArea"] textarea::-webkit-input-placeholder {
  color: #5f6368 !important;
  opacity: 1 !important;
  -webkit-text-fill-color: #5f6368 !important;
}

[data-testid="stChatInput"] textarea::-moz-placeholder,
[data-testid="stChatInputTextArea"] textarea::-moz-placeholder {
  color: #5f6368 !important;
  opacity: 1 !important;
}

[data-testid="stChatInput"] textarea::-webkit-scrollbar,
[data-testid="stChatInputTextArea"] textarea::-webkit-scrollbar {
  width: 8px !important;
}

[data-testid="stChatInput"] textarea::-webkit-scrollbar-track,
[data-testid="stChatInputTextArea"] textarea::-webkit-scrollbar-track {
  background: #e8eaed !important;
  border-radius: 999px !important;
}

[data-testid="stChatInput"] textarea::-webkit-scrollbar-thumb,
[data-testid="stChatInputTextArea"] textarea::-webkit-scrollbar-thumb {
  background: #9aa0a6 !important;
  border-radius: 999px !important;
}

[data-testid="stChatInput"] textarea::-webkit-scrollbar-thumb:hover,
[data-testid="stChatInputTextArea"] textarea::-webkit-scrollbar-thumb:hover {
  background: #5f6368 !important;
}

[data-testid="stChatInputSubmitButton"] {
  background: #0b57d0 !important;
  background-color: #0b57d0 !important;
  color: #ffffff !important;
  border: none !important;
  border-radius: 999px !important;
  box-shadow: none !important;
  opacity: 1 !important;
  flex: 0 0 auto !important;
  align-self: center !important;
  margin-left: auto !important;
}

[data-testid="stChatInputSubmitButton"]:disabled {
  background: #e8eaed !important;
  background-color: #e8eaed !important;
  color: #9aa0a6 !important;
  opacity: 1 !important;
}

/* Chat input: docked to bottom (same top/transform model as empty → smooth dock) */
[data-testid="stMain"]:has(.chat-active-state) [data-testid="stBottom"],
section.main:has(.chat-active-state) [data-testid="stBottom"] {
  position: fixed !important;
  top: 100% !important;
  bottom: auto !important;
  right: 0 !important;
  left: var(--chat-main-left, 0px) !important;
  width: auto !important;
  z-index: 1000 !important;
  padding: 0 !important;
  margin: 0 !important;
  background: var(--md-sys-color-surface) !important;
  border-top: 1px solid var(--md-sys-color-outline);
  transform: translateY(-100%) !important;
}

/* Gemini-style empty state: top-anchored so growth expands downward */
[data-testid="stMain"]:has(.chat-empty-state) [data-testid="stBottom"],
section.main:has(.chat-empty-state) [data-testid="stBottom"] {
  position: fixed !important;
  top: 46% !important;
  bottom: auto !important;
  right: 0 !important;
  left: var(--chat-main-left, 0px) !important;
  width: auto !important;
  z-index: 1000 !important;
  padding: 0 !important;
  margin: 0 !important;
  background: #f8f9fa !important;
  border-top: none !important;
  transform: none !important;
}

[data-testid="stBottomBlockContainer"] {
  width: 100% !important;
  max-width: 100% !important;
  padding-top: 0.65rem !important;
  padding-bottom: 0.65rem !important;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
  margin: 0 !important;
  background: #f8f9fa !important;
  box-sizing: border-box !important;
}

[data-testid="stMain"]:has(.chat-empty-state) [data-testid="stBottomBlockContainer"],
section.main:has(.chat-empty-state) [data-testid="stBottomBlockContainer"] {
  background: #f8f9fa !important;
  max-width: 100% !important;
  width: 100% !important;
  margin: 0 !important;
  padding-left: 1.5rem !important;
  padding-right: 1.5rem !important;
}

/* Collapsed sidebar handled by --chat-main-left sync script */
.stChatFloatingInputContainer,
[data-testid="stBottom"] > div {
  padding-bottom: 0 !important;
  margin-bottom: 0 !important;
}

footer {
  display: none !important;
}

div[data-testid="stTabs"] button {
  font-weight: 500 !important;
}

section[data-testid="stFileUploaderDropzone"] {
  border-radius: var(--md-radius-md) !important;
  border: 1px dashed var(--md-sys-color-outline) !important;
  background: var(--md-sys-color-surface-container-high) !important;
}

hr {
  border-color: var(--md-sys-color-outline) !important;
}

[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] span,
[data-testid="stSidebar"] small {
  color: #5f6368 !important;
  -webkit-text-fill-color: #5f6368 !important;
  opacity: 1 !important;
}

/* Grok-style Zero State UI */
.chat-empty-hero {
  display: flex !important;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.chat-empty-title {
  font-size: 2.25rem !important;
  font-weight: 700 !important;
  color: var(--md-sys-color-on-surface) !important;
  margin-bottom: 2rem !important;
  text-align: center;
  letter-spacing: -0.02em;
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  max-width: 600px;
  width: 100%;
}

.prompt-card {
  display: flex !important;
  flex-direction: column;
  align-items: flex-start;
  padding: 1rem 1.25rem;
  background: var(--md-sys-color-surface-container) !important;
  border: 1px solid var(--md-sys-color-outline-variant) !important;
  border-radius: 12px;
  cursor: pointer;
  transition: background-color 0.2s ease, border-color 0.2s ease, transform 0.1s ease;
}

.prompt-card:hover {
  background: var(--md-sys-color-surface-container-high) !important;
  border-color: var(--md-sys-color-outline) !important;
  transform: translateY(-2px);
}

.prompt-card:active {
  transform: translateY(0);
}

.prompt-icon {
  font-family: "Material Symbols Outlined" !important;
  font-size: 24px;
  color: var(--md-sys-color-on-surface-variant);
  margin-bottom: 0.75rem;
  font-variation-settings: "FILL" 0, "wght" 400, "GRAD" 0, "opsz" 24;
}

.prompt-text {
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--md-sys-color-on-surface);
  line-height: 1.4;
}

@media (max-width: 640px) {
  .prompt-grid {
    grid-template-columns: 1fr;
  }
}
</style>
"""


def inject_styles() -> None:
    """Inject global app CSS into the Streamlit page."""
    import streamlit as st

    theme_type = "light"
    try:
        # st.context.theme is a Dict-like object representing the active theme config
        if hasattr(st.context, "theme") and st.context.theme and getattr(st.context.theme, "type", None) == "dark":
            theme_type = "dark"
    except Exception:
        pass

    # Override with user preference if present
    app_theme_control = st.session_state.get("app_theme_control", "System")
    if app_theme_control == "Light":
        theme_type = "light"
    elif app_theme_control == "Dark":
        theme_type = "dark"

    theme_vars = ""
    if theme_type == "dark":
        theme_vars = """
        :root {
          --md-sys-color-primary: #ffffff;
          --md-sys-color-on-primary: #000000;
          --md-sys-color-primary-container: #111111;
          --md-sys-color-on-primary-container: #ffffff;
          --md-sys-color-secondary-container: #222222;
          --md-sys-color-on-secondary-container: #a0a0a0;
          --md-sys-color-surface: #000000;
          --md-sys-color-surface-container: #111111;
          --md-sys-color-surface-container-high: #222222;
          --md-sys-color-on-surface: #ffffff;
          --md-sys-color-on-surface-variant: #a0a0a0;
          --md-sys-color-outline: #333333;
          --md-sys-color-outline-variant: #222222;
          --md-elevation-1: 0 1px 3px rgba(0,0,0,0.6);
          --md-elevation-2: 0 2px 6px rgba(0,0,0,0.6);
        }
        .stApp {
          background-color: #000000 !important;
          color: #ffffff !important;
        }
        .bubble-user {
          background: #111111 !important;
          color: #ffffff !important;
          border-color: #333333 !important;
        }
        .bubble-user .bubble-label {
          color: #a0a0a0 !important;
        }
        .bubble-user p, .bubble-user span:not(.bubble-label) {
          color: #ffffff !important;
        }
        .bubble-assistant {
          background: #000000 !important;
          color: #ffffff !important;
          border-color: transparent !important;
        }
        .bubble-assistant, .bubble-assistant p, .bubble-assistant span:not(.bubble-label):not(.type-pill):not(.score-pill),
        .assistant-answer, .assistant-answer p, .assistant-answer span:not(.bubble-label):not(.type-pill):not(.score-pill),
        .typing-text, .typing-row {
          color: #ffffff !important;
        }
        .score-pill {
          background: #333333 !important;
          color: #ffffff !important;
        }
        .type-pill, .hit-pill {
          background: #222222 !important;
          color: #ffffff !important;
        }
        .avatar-user {
          background: #333333 !important;
          color: #ffffff !important;
        }
        .avatar-assistant {
          background: #111111 !important;
          color: #ffffff !important;
          border: 1px solid #333333 !important;
        }
        /* Admin overrides for dark mode */
        .block-container:has(.admin-page-marker) {
          color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stMarkdownContainer"] :is(p, span, li, h1, h2, h3, h4),
        .block-container:has(.admin-page-marker) label,
        .block-container:has(.admin-page-marker) [data-baseweb="select"] > div,
        .block-container:has(.admin-page-marker) [data-baseweb="input"] input,
        .block-container:has(.admin-page-marker) [data-testid="stTextInput"] input,
        .block-container:has(.admin-page-marker) div[data-testid="stTabs"] button,
        .block-container:has(.admin-page-marker) [data-testid="stFileUploaderDropzoneInstructions"],
        .block-container:has(.admin-page-marker) [data-testid="stFileUploaderDropzoneInstructions"] span {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stCaptionContainer"],
        .block-container:has(.admin-page-marker) .stCaption {
          color: #a0a0a0 !important;
          -webkit-text-fill-color: #a0a0a0 !important;
        }
        .block-container:has(.admin-page-marker) :is(
          [data-testid="stNumberInputContainer"],
          [data-testid="stTextInputRootElement"],
          [data-testid="stTextAreaRootElement"]
        ) {
          background-color: #111111 !important;
          background: #111111 !important;
          border-color: #333333 !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) :is(
          [data-testid="stNumberInputField"],
          [data-testid="stTextInput"] input,
          [data-testid="stTextArea"] textarea
        ) {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          caret-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) :is(
          [data-testid="stSelectbox"],
          [data-testid="stMultiSelect"]
        ) div:has(> input) {
          background-color: #111111 !important;
          background: #111111 !important;
          border-color: #333333 !important;
        }
        .block-container:has(.admin-page-marker) :is(
          [data-testid="stSelectbox"],
          [data-testid="stMultiSelect"]
        ) input {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          caret-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stWidgetLabel"],
        .block-container:has(.admin-page-marker) [data-testid="stWidgetLabel"] p {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) section[data-testid="stFileUploaderDropzone"] {
          background: #111111 !important;
          border-color: #333333 !important;
        }
        .block-container:has(.admin-page-marker) section[data-testid="stFileUploaderDropzone"] :is(
          button,
          span,
          small,
          p,
          div
        ) {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) section[data-testid="stFileUploaderDropzone"] button {
          background: #111111 !important;
          border-color: #333333 !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stFileChips"],
        .block-container:has(.admin-page-marker) [data-testid="stFileChip"] {
          background: #111111 !important;
          background-color: #111111 !important;
          border-color: #333333 !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stFileChip"] :is(
          [data-testid="stFileChipName"],
          span,
          p,
          small,
          div
        ) {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) div[data-testid="stTabs"] button[aria-selected="true"] {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        /* Admin card */
        .block-container:has(.admin-page-marker) div[data-testid="stHorizontalBlock"]:has(.doc-row) {
          background: #111111 !important;
          border-color: #333333 !important;
        }
        .doc-row-name {
          color: #ffffff !important;
        }
        .doc-row-icon {
          color: #ffffff !important;
        }
        /* Expander overrides */
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] {
          background: #111111 !important;
          border-color: #333333 !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] details {
          background: #111111 !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] summary,
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] .streamlit-expanderHeader,
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stExpanderDetails"],
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stExpanderIcon"] {
          background: #000000 !important;
          background-color: #000000 !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] summary :is(p, span, div, label),
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] .streamlit-expanderHeader :is(p, span, div, label),
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] summary svg,
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] .streamlit-expanderHeader svg,
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stExpanderToggleIcon"] svg {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          fill: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] summary,
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stExpanderDetails"] {
          border-bottom-color: #333333 !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stExpander"] [data-testid="stMarkdownContainer"] :is(p, span, li, h1, h2, h3, h4) {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        /* Chat input text color */
        [data-testid="stChatInput"] {
          background: #111111 !important;
          background-color: #111111 !important;
          border-color: #333333 !important;
        }
        [data-testid="stChatInput"] textarea {
          color: #ffffff !important;
          caret-color: #ffffff !important;
        }
        .source-mini-card {
          background: #111111 !important;
          border-color: #333333 !important;
        }
        .source-mini-file {
          color: #ffffff !important;
        }
        .source-mini-meta, .source-mini-heading {
          color: #a0a0a0 !important;
        }
        .src-nav-btn {
          background: #111111 !important;
          color: #ffffff !important;
          border-color: #333333 !important;
        }
        .src-nav-btn:hover {
          background: #222222 !important;
          color: #ffffff !important;
          border-color: #ffffff !important;
        }
        .stChatFloatingInputContainer,
        [data-testid="stBottom"],
        [data-testid="stBottom"] > div,
        [data-testid="stBottomBlockContainer"] {
          background: #000000 !important;
          background-color: #000000 !important;
        }
        
        /* Sidebar buttons */
        [data-testid="stSidebar"] .stButton > button,
        [data-testid="stSidebar"] .stButton > button[kind="primary"],
        [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
          background: #111111 !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          border-color: #333333 !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover,
        [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
          background: #222222 !important;
          border-color: #ffffff !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        [data-testid="stSidebar"] .stButton > button:hover p,
        [data-testid="stSidebar"] .stButton > button:hover div,
        [data-testid="stSidebar"] .stButton > button:hover span {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        
        /* Primary (Active) Sidebar button accent */
        [data-testid="stSidebar"] .stButton > button[kind="primary"],
        [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
          background: #222222 !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
          border-color: #555555 !important;
        }
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover,
        [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"]:hover {
          background: #333333 !important;
          border-color: #ffffff !important;
        }
        
        /* Input Placeholders */
        .block-container:has(.admin-page-marker) :is(
          [data-testid="stTextInput"],
          [data-testid="stNumberInput"],
          [data-testid="stTextArea"]
        ) :is(input, textarea)::placeholder {
          color: #8c9096 !important;
          -webkit-text-fill-color: #8c9096 !important;
        }
        
        /* Checkboxes/Toggles Label & Bg */
        .block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) [data-testid="stWidgetLabel"],
        .block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) [data-testid="stWidgetLabel"] p {
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        .block-container:has(.admin-page-marker) [data-testid="stCheckbox"]:not(:has(svg)) > *:not([data-selected]) > div:has(> div):not([data-testid="stWidgetLabel"]) {
          background-color: #333333 !important;
          border-color: #222222 !important;
        }
        
        /* Inline Code Blocks in Captions */
        .block-container:has(.admin-page-marker) [data-testid="stCaptionContainer"] code,
        .block-container:has(.admin-page-marker) .stCaption code {
          background: rgba(255, 255, 255, 0.15) !important;
          color: #ffffff !important;
          -webkit-text-fill-color: #ffffff !important;
        }
        """

    image_search_styles = """
    .bubble-image-thumb {
      max-width: 140px;
      max-height: 140px;
      border-radius: 8px;
      margin-top: 5px;
      cursor: pointer;
      display: block;
      border: 1px solid var(--md-sys-color-outline);
    }
    .image-match-badge {
      display: inline-flex;
      align-items: center;
      background: var(--md-sys-color-primary-container);
      color: var(--md-sys-color-primary);
      border-radius: 999px;
      padding: 0.12rem 0.5rem;
      font-size: 0.7rem;
      font-weight: 500;
      margin-left: 5px;
    }
    """

    st.markdown(APP_CSS + f"<style>{theme_vars}\n{image_search_styles}</style>", unsafe_allow_html=True)

