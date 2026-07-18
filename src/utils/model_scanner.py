import streamlit as st
from openai import OpenAI
from src.config import Settings

FREE_OPENROUTER_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "qwen/qwen3-coder:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "poolside/laguna-xs-2.1:free",
    "cohere/north-mini-code:free",
    "nvidia/nemotron-3.5-content-safety:free",
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
    "liquid/lfm-2.5-1.2b-instruct:free",
]

@st.cache_data(show_spinner=False)
def get_available_models(
    openai_api_key: str, 
    openai_base_url: str, 
    gemini_api_key: str,
    openrouter_api_key: str,
    openrouter_base_url: str
) -> list[tuple[str, str]]:
    """Fetch available models from configured providers and cache them as (Provider, ID)."""
    models_set = set()

    # 1. Fetch from standard configured OpenAI API (could be a custom portal or OpenAI origin)
    if openai_api_key:
        try:
            kwargs = {"api_key": openai_api_key}
            if openai_base_url:
                kwargs["base_url"] = openai_base_url
            client = OpenAI(**kwargs)
            res = client.models.list()
            for m in res.data:
                models_set.add(("OpenAI", m.id))
        except Exception:
            pass

    # 2. Add Gemini models if key is present
    if gemini_api_key:
        models_set.add(("Google Gemini", "gemini-1.5-flash"))
        models_set.add(("Google Gemini", "gemini-1.5-pro"))
        models_set.add(("Google Gemini", "gemini-2.0-flash-exp"))

    # 3. Add Free OpenRouter models if OpenRouter API is configured
    if openrouter_api_key:
        for m in FREE_OPENROUTER_MODELS:
            models_set.add(("OpenRouter", m))

    # Convert to list and sort for stable UI drop box display
    sorted_models = sorted(list(models_set))
    
    return sorted_models if sorted_models else [("OpenAI", "gpt-4o-mini")]
