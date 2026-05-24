"""Tests for POST /run and related endpoints."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


async def _fake_pipeline(session_id, query, ctx):
    """Simulate a fast pipeline completion without hitting an LLM."""
    from app.schema import MarketReport

    await ctx.add_event("agent_start", "Researcher", f"Starting research for: {query}")
    await ctx.add_event("agent_end", "Researcher", "Done")
    await ctx.add_event("agent_start", "Reporter", "Writing report")
    await ctx.add_event("agent_end", "Reporter", "Complete")

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


async def test_add_event_is_coroutine():
    """ResearchContext.add_event must be async so sub-agent awaits work correctly."""
    import inspect

    from app.context import ResearchContext

    ctx = ResearchContext(tavily_api_key="", db_connection=None, session_state=None)
    assert inspect.iscoroutinefunction(ctx.add_event)


async def test_streaming_context_enqueues_event():
    """StreamingResearchContext.add_event should append to events list."""
    from api.stream import StreamingResearchContext

    ctx = StreamingResearchContext(tavily_api_key="", db_connection=None, session_state=None)
    await ctx.add_event("agent_limit", "Researcher", "Hit limit")
    assert len(ctx.events) == 1
    assert ctx.events[0].event_type == "agent_limit"
    ctx.close_stream()


async def test_mark_error_persists_failed_stage(client):
    """mark_error should store failed_stage in the DB row."""
    from api.db_sessions import get_session, insert_session, mark_error

    await insert_session("sess_stage_test", "some query")
    await mark_error("sess_stage_test", "boom", "[]", failed_stage="pipeline")
    row = await get_session("sess_stage_test")
    assert row is not None
    assert row["failed_stage"] == "pipeline"
    assert row["status"] == "error"


# ---------------------------------------------------------------------------
# Scenario E — Retry route dispatches to the right resume strategy
# ---------------------------------------------------------------------------


async def _seed_failed_session(
    session_id: str,
    *,
    research_json: str | None = None,
    analyst_json: str | None = None,
) -> None:
    """Insert a failed session row, optionally with checkpoint findings."""
    from api.db_sessions import (
        insert_session,
        mark_error,
        save_analyst_checkpoint,
        save_research_checkpoint,
    )

    await insert_session(session_id, "retry query")
    if research_json is not None:
        await save_research_checkpoint(session_id, research_json)
    if analyst_json is not None:
        await save_analyst_checkpoint(session_id, analyst_json)
    await mark_error(session_id, "earlier failure", "[]", failed_stage="pipeline")


async def _noop_async(*args, **kwargs):
    """Stand-in awaitable used to patch pipeline coroutines."""
    return None


async def test_retry_no_checkpoints_runs_full_pipeline(client):
    """E1: No checkpoints → POST /retry dispatches to _run_pipeline."""
    await _seed_failed_session("sess_e1")

    pipeline_mock = AsyncMock(side_effect=_noop_async)
    reporter_mock = AsyncMock(side_effect=_noop_async)
    with patch("api.routes.run._run_pipeline", new=pipeline_mock):
        with patch("api.routes.run._run_reporter_only", new=reporter_mock):
            response = await client.post("/run/sess_e1/retry")
            await asyncio.sleep(0.01)  # let the background task be scheduled

    assert response.status_code == 202
    assert pipeline_mock.await_count == 1
    assert reporter_mock.await_count == 0


async def test_retry_research_only_runs_full_pipeline(client):
    """E2: research_json present, analyst_json missing → _run_pipeline."""
    from app.schema import MarketAccessFindings

    research_payload = MarketAccessFindings(
        raw_evidence_summary="prior research"
    ).model_dump_json()
    await _seed_failed_session("sess_e2", research_json=research_payload)

    pipeline_mock = AsyncMock(side_effect=_noop_async)
    reporter_mock = AsyncMock(side_effect=_noop_async)
    with patch("api.routes.run._run_pipeline", new=pipeline_mock):
        with patch("api.routes.run._run_reporter_only", new=reporter_mock):
            response = await client.post("/run/sess_e2/retry")
            await asyncio.sleep(0.01)

    assert response.status_code == 202
    assert pipeline_mock.await_count == 1
    assert reporter_mock.await_count == 0


async def test_retry_both_checkpoints_runs_reporter_only(client):
    """E3: Both research_json and analyst_json present → _run_reporter_only."""
    from app.schema import AnalystFindings, MarketAccessFindings

    research_payload = MarketAccessFindings(
        raw_evidence_summary="prior research"
    ).model_dump_json()
    analyst_payload = AnalystFindings(summary="prior analysis").model_dump_json()
    await _seed_failed_session(
        "sess_e3",
        research_json=research_payload,
        analyst_json=analyst_payload,
    )

    pipeline_mock = AsyncMock(side_effect=_noop_async)
    reporter_mock = AsyncMock(side_effect=_noop_async)
    with patch("api.routes.run._run_pipeline", new=pipeline_mock):
        with patch("api.routes.run._run_reporter_only", new=reporter_mock):
            response = await client.post("/run/sess_e3/retry")
            await asyncio.sleep(0.01)

    assert response.status_code == 202
    assert reporter_mock.await_count == 1
    assert pipeline_mock.await_count == 0


async def test_retry_analyst_only_falls_back_to_full_pipeline(client):
    """E4: analyst_json present but research_json missing → _run_pipeline fallback."""
    from app.schema import AnalystFindings

    analyst_payload = AnalystFindings(summary="prior analysis").model_dump_json()
    await _seed_failed_session("sess_e4", analyst_json=analyst_payload)

    pipeline_mock = AsyncMock(side_effect=_noop_async)
    reporter_mock = AsyncMock(side_effect=_noop_async)
    with patch("api.routes.run._run_pipeline", new=pipeline_mock):
        with patch("api.routes.run._run_reporter_only", new=reporter_mock):
            response = await client.post("/run/sess_e4/retry")
            await asyncio.sleep(0.01)

    assert response.status_code == 202
    assert pipeline_mock.await_count == 1
    assert reporter_mock.await_count == 0


async def test_retry_endpoint_reads_failed_stage_from_db(client):
    """E5/AC10: mark_error's failed_stage column must be readable by the retry
    endpoint flow — the retry route looks up the original session via
    get_session, so confirm get_session returns the failed_stage we wrote."""
    from api.db_sessions import get_session

    await _seed_failed_session("sess_failed_stage_retry")

    pipeline_mock = AsyncMock(side_effect=_noop_async)
    with patch("api.routes.run._run_pipeline", new=pipeline_mock):
        response = await client.post("/run/sess_failed_stage_retry/retry")

    assert response.status_code == 202
    row = await get_session("sess_failed_stage_retry")
    assert row is not None
    assert row["failed_stage"] == "pipeline"


async def test_retry_unknown_session_returns_404(client):
    """Retry endpoint must 404 when the original session id is unknown."""
    response = await client.post("/run/nonexistent_session/retry")
    assert response.status_code == 404
