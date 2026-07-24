# Token & Cost Tracker — Global Usage Dashboard

Add a centralized token counting and cost estimation system that tracks every LLM/embedding API call across the entire app, with a mini sidebar widget and a full expanded dashboard tab in Admin.

## Decisions (From User Feedback)

✅ **Token counting:** Option 2 — Intercept real `usage` data from API responses via LangChain callbacks. Fall back to `tiktoken` only for preview estimation.  
✅ **Persistence:** Mini sidebar widget shows **current session only**. Full usage log is **persisted to a local JSON file** and viewable as history in the expanded Admin dashboard.  
✅ **Budget alerts:** Configurable budget input saved to `.env` or a local config file. Default threshold: **$5.00**.  
✅ **Pricing:** Comprehensive pricing dict with verified prices annotated. Unknown prices marked with `# VERIFY` comments.

---

## Proposed Changes

### Token Tracking Core (`src/utils/`)

#### [NEW] [model_pricing.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/src/utils/model_pricing.py)

A pricing registry mapping model IDs → `(input_cost_per_1M_tokens, output_cost_per_1M_tokens)`:

```python
# Prices in USD per 1 million tokens — (input, output)
# Sources: official pricing pages as of July 2026
# Models marked "# VERIFY" need you to confirm the exact price

MODEL_PRICING: dict[str, tuple[float, float]] = {
    # ── OpenAI (via portal) ──────────────────────────────
    "gpt-4o-mini":            (0.15,   0.60),
    "gpt-4o":                 (2.50,  10.00),
    "gpt-4-turbo":            (10.00, 30.00),
    "gpt-3.5-turbo":          (0.50,   1.50),

    # ── Google Gemini ────────────────────────────────────
    "gemini-2.5-flash":       (0.15,   0.60),    # VERIFY — may have changed
    "gemini-2.0-flash-exp":   (0.10,   0.40),    # VERIFY — experimental
    "gemini-1.5-flash":       (0.075,  0.30),
    "gemini-1.5-pro":         (1.25,   5.00),

    # ── OpenRouter FREE models (all $0.00) ───────────────
    "meta-llama/llama-3.3-70b-instruct:free":              (0.0, 0.0),
    "meta-llama/llama-3.2-3b-instruct:free":               (0.0, 0.0),
    "google/gemma-4-31b-it:free":                          (0.0, 0.0),
    "google/gemma-4-26b-a4b-it:free":                      (0.0, 0.0),
    "qwen/qwen3-coder:free":                               (0.0, 0.0),
    "nousresearch/hermes-3-llama-3.1-405b:free":           (0.0, 0.0),
    "poolside/laguna-xs-2.1:free":                         (0.0, 0.0),
    "cohere/north-mini-code:free":                         (0.0, 0.0),
    "nvidia/nemotron-3.5-content-safety:free":             (0.0, 0.0),
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free":  (0.0, 0.0),
    "liquid/lfm-2.5-1.2b-thinking:free":                   (0.0, 0.0),
    "liquid/lfm-2.5-1.2b-instruct:free":                   (0.0, 0.0),

    # ── OpenRouter PAID models ───────────────────────────
    "mistralai/pixtral-12b":  (0.15,   0.15),

    # ── Embeddings ───────────────────────────────────────
    "text-embedding-3-small": (0.02,   0.00),
    "text-embedding-3-large": (0.13,   0.00),
}
```

Also includes:
- `get_cost(model, input_tokens, output_tokens) -> float` — calculates USD cost.
- `get_pricing(model) -> tuple[float, float]` — lookup with `:free` suffix wildcard fallback.
- Returns `(0.0, 0.0)` for any unknown model (safe default, logged as warning).

#### [NEW] [token_tracker.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/src/utils/token_tracker.py)

A `TokenTracker` class that uses `st.session_state` for current session and a **persistent JSON log file** (`usage_log.json` in project root) for history:

```python
@dataclass
class UsageRecord:
    timestamp: str          # ISO format
    model: str
    provider: str           # "OpenAI" | "Google Gemini" | "OpenRouter"
    operation: str          # "chat" | "embedding" | "caption" | "ingest"
    input_tokens: int
    output_tokens: int
    estimated_cost: float   # USD

class TokenTracker:
    def record(self, ...) -> None
        """Append to session list AND persist to JSON log file."""

    def get_session_totals(self) -> dict
        """Returns {total_input, total_output, total_cost, num_calls} for current session."""

    def get_breakdown_by_model(self) -> list[dict]
        """Group session records by model."""

    def get_all_history(self) -> list[UsageRecord]
        """Load ALL records from persistent JSON file (across sessions)."""

    def reset_session(self) -> None
        """Clear current session counters (does NOT delete persistent history)."""

    def clear_history(self) -> None
        """Delete the persistent JSON log file entirely."""

    def export_csv(self) -> str
        """Return all persistent history as CSV string for download."""
```

#### [NEW] [budget.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/src/utils/budget.py)

Small utility for budget management:
- Reads/writes budget threshold to a local file (`budget_config.json`).
- Default: `$5.00`.
- `get_budget() -> float`, `set_budget(value: float) -> None`.
- `check_budget(current_cost: float) -> bool` — returns `True` if over budget.

---

### LangChain Callback Integration (`src/lc/`)

#### [MODIFY] [chain.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/src/lc/chain.py)

- Add a `CostTrackingCallback(BaseCallbackHandler)` that:
  - Captures `on_llm_end(response)` → extracts `response.llm_output["token_usage"]` or `response.generations[0].generation_info["usage_metadata"]`.
  - Calls `TokenTracker.record(...)` with model name, provider, and token counts.
- Modify `LangChainGroundedGenerator.generate()` to pass the callback to `chain.invoke(..., config={"callbacks": [cost_cb]})`.

#### [MODIFY] [embeddings.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/src/lc/embeddings.py)

- Create a wrapper class `TrackedEmbeddings` that wraps `OpenAIEmbeddings`.
- After each `embed_documents()` or `embed_query()`, use `tiktoken` to estimate token count (embedding APIs often omit usage in LangChain responses).
- Record to `TokenTracker` with `operation="embedding"`.

---

### Visual Caption Tracking

#### [MODIFY] [visual_caption.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/src/ingest/visual_caption.py)

- In `_caption_gemini()`: extract `response.usage_metadata.prompt_token_count` and `response.usage_metadata.candidates_token_count` → record to tracker.
- In `_caption_openai()`: extract `response.usage.prompt_tokens` and `response.usage.completion_tokens` → record to tracker.
- Operation type: `"caption"`.

---

### Sidebar Mini Widget

#### [MODIFY] [app.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/app.py)

Add a compact cost card at the bottom of the sidebar (below theme control):

```
┌───────────────────────────┐
│  💰 Session Usage         │
│  📥 In: 8,230 tokens      │
│  📤 Out: 4,120 tokens     │
│  💵 Cost: $0.0019         │
│  ━━━━━━━━━━━━━━━━━ 38%    │  ← budget progress bar
│  [📊 View Details]        │  ← navigates to Admin
└───────────────────────────┘
```

- **Budget progress bar:** Visual bar showing `current_cost / budget_threshold`. Turns yellow at 70%, red at 90%.
- **"View Details" button:** Sets `sidebar_page = "Admin"` and auto-opens the Usage tab.
- **Session-only data** — resets when the app restarts.

---

### Admin Expanded Dashboard

#### [MODIFY] [admin_page.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/src/ui/admin_page.py)

Add a new section/tab called **"📊 Usage & Cost"** containing:

**1. Budget Configuration:**
- Number input for budget threshold (default $5.00).
- "Save" button → persists to `budget_config.json`.
- Warning alert if current total exceeds budget.

**2. Current Session Summary (4 metric cards):**
| Total Input Tokens | Total Output Tokens | Total Cost ($) | API Calls |
|---|---|---|---|
| 12,450 | 6,230 | $0.0032 | 8 |

**3. Session Breakdown Table:**
- Columns: `Model` | `Provider` | `Operation` | `Input Tokens` | `Output Tokens` | `Cost ($)` | `# Calls`
- Grouped by model with subtotals.

**4. Historical Usage Log (Persistent):**
- Scrollable table loaded from `usage_log.json` showing ALL past sessions.
- Columns: `Timestamp` | `Model` | `Operation` | `Input` | `Output` | `Cost`
- Filter by date range.
- **"Export CSV"** download button.
- **"Clear History"** button (with confirmation).

**5. Session Controls:**
- **"Reset Session"** button — clears current session counters only.

---

### Styles

#### [MODIFY] [styles.py](file:///c:/Users/sonvu/Documents/Project/chat_bot_rag/src/ui/styles.py)

- CSS for sidebar mini-widget: compact card, subtle gradient, monospace numbers, budget progress bar with color transitions.
- CSS for Admin dashboard: metric cards row, table styling, alert box for budget warnings.

---

## File Summary

| File | Action | Purpose |
|:---|:---|:---|
| `src/utils/model_pricing.py` | **NEW** | Model pricing registry + cost calculator |
| `src/utils/token_tracker.py` | **NEW** | Session tracker + persistent JSON logger |
| `src/utils/budget.py` | **NEW** | Budget threshold read/write/check |
| `src/lc/chain.py` | MODIFY | Add LangChain callback to capture LLM token usage |
| `src/lc/embeddings.py` | MODIFY | Wrap embeddings with tiktoken estimation |
| `src/ingest/visual_caption.py` | MODIFY | Extract usage from caption API responses |
| `app.py` | MODIFY | Add sidebar mini-widget |
| `src/ui/admin_page.py` | MODIFY | Add "Usage & Cost" dashboard tab |
| `src/ui/styles.py` | MODIFY | Add widget + dashboard CSS |

---

## Verification Plan

### Manual Verification
1. Send 2-3 chat messages → sidebar widget updates token count and cost in real-time.
2. Switch between OpenAI / Gemini / OpenRouter free models → verify correct pricing ($0 for free models).
3. Upload a PDF with images in Admin → verify embedding + caption tokens are tracked.
4. Click "View Details" in sidebar → navigates to Admin Usage tab.
5. Set budget to $0.01, send a message → verify yellow/red warning appears.
6. Restart the app → verify session counters reset but history is still visible in Admin.
7. Click "Export CSV" → valid CSV downloads with all historical records.
8. Click "Clear History" → persistent log is deleted.
