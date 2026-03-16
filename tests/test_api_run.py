"""Tests for POST /run and related endpoints."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


async def _fake_pipeline(session_id, query, ctx):
    """Simulate a fast pipeline completion without hitting an LLM."""
    from app.schema import MarketReport

    ctx.add_event("agent_start", "Researcher", f"Starting research for: {query}")
    ctx.add_event("agent_end", "Researcher", "Done")
    ctx.add_event("agent_start", "Reporter", "Writing report")
    ctx.add_event("agent_end", "Reporter", "Complete")

    report = MarketReport(
        title="Test Report",
        executive_summary="Test summary",
        sections=[],
        sources=[],
        markdown_content="# Test\n",
    )

    from api.db_sessions import mark_complete
    import json as _json

    await mark_complete(
        session_id=session_id,
        report_json=report.model_dump_json(),
        events_json=_json.dumps([e.model_dump(mode="json") for e in ctx.events]),
        usage_json="{}",
    )
    ctx.close_stream()


async def test_post_run_returns_202(client):
    """POST /run should return 202 with session_id and stream_url."""
    with patch("api.routes.run._run_pipeline", side_effect=_fake_pipeline):
        response = await client.post(
            "/run",
            json={"query": "GLP-1 market size", "tavily_api_key": ""},
        )
    assert response.status_code == 202
    data = response.json()
    assert "session_id" in data
    assert "stream_url" in data
    assert data["stream_url"].startswith("/run/")


async def test_post_run_missing_query(client):
    """POST /run without query should return 422."""
    response = await client.post("/run", json={})
    assert response.status_code == 422


async def test_stream_not_found(client):
    """GET /run/{id}/stream for unknown session should return 404."""
    response = await client.get("/run/nonexistent_session_id/stream")
    assert response.status_code == 404


async def test_pdf_not_found_for_unknown_session(client):
    """GET /sessions/{id}/pdf for unknown session should return 404."""
    response = await client.get("/sessions/nonexistent_id/pdf")
    assert response.status_code == 404


async def test_pdf_not_found_without_report(client):
    """GET /sessions/{id}/pdf for session without report should return 404."""
    from api.db_sessions import insert_session

    await insert_session("sess_no_report", "A query with no report")
    response = await client.get("/sessions/sess_no_report/pdf")
    assert response.status_code == 404
