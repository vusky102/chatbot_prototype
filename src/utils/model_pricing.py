from __future__ import annotations

# Prices in USD per 1 million tokens — (input, output)
# Sources: official pricing pages as of July 2026
# Models marked "# VERIFY" need you to confirm the exact price

MODEL_PRICING: dict[str, tuple[float, float]] = {
    # ── OpenAI (via portal) ──────────────────────────────
    "gpt-4o-mini":            (0.17,   0.66),
    "gpt-4.1-mini":           (0.40,   1.60),
    "gpt-5.4-mini":           (0.25,   2.00),
    "gpt-4o":                 (2.50,  10.00),
    "gpt-4-turbo":            (10.00, 30.00),
    "gpt-3.5-turbo":          (0.50,   1.50),
    "deepseek-v4-flash":      (0.19,   0.51),

    # ── Google Gemini ────────────────────────────────────
    "gemini-2.5-flash":       (0.30,   2.50),    # VERIFY — may have changed
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


def get_pricing(model_id: str) -> tuple[float, float]:
    """Return (input_cost_per_1M, output_cost_per_1M) in USD.
    Gracefully handles :free models and unknown models.
    """
    model_id = model_id.lower().strip()
    
    if model_id in MODEL_PRICING:
        return MODEL_PRICING[model_id]
        
    if model_id.endswith(":free"):
        return (0.0, 0.0)
        
    return (0.0, 0.0)


def get_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the estimated cost in USD based on token counts."""
    in_price_1m, out_price_1m = get_pricing(model_id)
    
    in_cost = (input_tokens / 1_000_000.0) * in_price_1m
    out_cost = (output_tokens / 1_000_000.0) * out_price_1m
    
    return in_cost + out_cost
