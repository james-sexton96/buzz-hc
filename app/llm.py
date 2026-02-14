"""Configurable LLM layer: Ollama by default, extensible to OpenAI/Google/Anthropic."""

import os
from typing import Any

from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider


def get_model() -> Any:
    """
    Return the configured chat model from environment.

    Environment variables:
        LLM_PROVIDER: One of 'ollama' (default), 'openai'. Future: 'anthropic', 'google'.
        LLM_MODEL: Model name (e.g. ministral-3, glm4.7-flash for Ollama).
        OLLAMA_BASE_URL: Ollama API base URL (default http://localhost:11434/v1).
        OPENAI_API_KEY: Required when LLM_PROVIDER=openai.
        ANTHROPIC_API_KEY: Required when LLM_PROVIDER=anthropic (not yet implemented).
        GOOGLE_API_KEY: Required when LLM_PROVIDER=google (not yet implemented).
    """
    provider = (os.environ.get("LLM_PROVIDER") or "ollama").strip().lower()
    model_name = os.environ.get("LLM_MODEL") or "ministral-3"

    if provider == "ollama":
        base_url = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434/v1"
        return OpenAIChatModel(
            model_name,
            provider=OllamaProvider(base_url=base_url),
        )

    if provider == "openai":
        from pydantic_ai.providers.openai import OpenAIProvider

        api_key = os.environ.get("OPENAI_API_KEY") or ""
        return OpenAIChatModel(
            model_name or "gpt-4o-mini",
            provider=OpenAIProvider(api_key=api_key),
        )

    if provider == "anthropic":
        from pydantic_ai.models.anthropic import AnthropicModel
        from pydantic_ai.providers.anthropic import AnthropicProvider

        api_key = os.environ.get("ANTHROPIC_API_KEY") or ""
        return AnthropicModel(
            model_name or "claude-3-5-sonnet-20241022",
            provider=AnthropicProvider(api_key=api_key),
        )

    if provider == "google":
        from pydantic_ai.models.google import GoogleModel
        from pydantic_ai.providers.google import GoogleProvider

        api_key = os.environ.get("GOOGLE_API_KEY") or ""
        return GoogleModel(
            model_name or "gemini-2.0-flash",
            provider=GoogleProvider(api_key=api_key),
        )

    # Default: Ollama
    base_url = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434/v1"
    return OpenAIChatModel(
        model_name,
        provider=OllamaProvider(base_url=base_url),
    )
