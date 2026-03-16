"""GET /config/scenarios and GET /config/health endpoints."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter

from app.scenarios import SCENARIOS
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()


@router.get("/config/scenarios")
async def get_scenarios() -> list[dict[str, Any]]:
    """Return predefined research scenario presets."""
    return SCENARIOS


@router.get("/config/health")
async def health_check() -> dict[str, Any]:
    """Return LLM provider info and API health status."""
    provider = (os.environ.get("LLM_PROVIDER") or "ollama").strip().lower()
    model = os.environ.get("LLM_MODEL") or "qwen3.5:latest"
    base_url = os.environ.get("OLLAMA_BASE_URL") or "http://localhost:11434/v1"
    tavily_configured = bool(os.environ.get("TAVILY_API_KEY", "").strip())

    return {
        "status": "ok",
        "llm_provider": provider,
        "llm_model": model,
        "ollama_base_url": base_url if provider == "ollama" else None,
        "tavily_configured": tavily_configured,
    }
