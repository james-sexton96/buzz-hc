"""Configurable LLM layer: Ollama by default, extensible to OpenAI/Google/Anthropic."""

import os
from collections.abc import Sequence
from typing import Any

from openai.types import chat
from pydantic_ai.messages import ModelMessage
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.ollama import OllamaProvider


class OllamaChatModel(OpenAIChatModel):
    """Workarounds for Ollama's OpenAI-compatible API quirks.

    Two known issues:
    1. content: null on tool-call-only assistant turns → 400 "invalid content type: <nil>"
    2. Literal newlines in content strings → 500 "invalid character '\\n' in string literal"
       (Ollama's Go JSON parser is stricter than Python's — it trips on content that
       the openai SDK serializes correctly but Ollama re-parses badly on its end.)
    """

    async def _map_messages(
        self,
        messages: Sequence[ModelMessage],
        model_request_parameters: Any,
    ) -> list[chat.ChatCompletionMessageParam]:
        result = await super()._map_messages(messages, model_request_parameters)
        for msg in result:
            # Fix null content on assistant messages (issue 1)
            if msg.get("content") is None and msg.get("role") == "assistant":
                msg["content"] = ""
            # Sanitize content strings for Ollama's picky parser (issue 2)
            content = msg.get("content")
            if isinstance(content, str):
                msg["content"] = content.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        return result


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
        return OllamaChatModel(
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
    return OllamaChatModel(
        model_name,
        provider=OllamaProvider(base_url=base_url),
    )


def get_retries() -> int:
    """Return the configured agent output validation retry count."""
    return int(os.environ.get("AGENT_RETRIES", "3"))
