"""POST /run and GET /run/{id}/stream (SSE) endpoints."""

from __future__ import annotations

import asyncio
import json
import os
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic_ai import UsageLimits

from api.database import init_db
from api.db_sessions import (
    get_session,
    insert_session,
    mark_complete,
    mark_error,
    save_analyst_checkpoint,
    save_research_checkpoint,
)
from api.stream import StreamingResearchContext
from app.history import UsageStats, generate_session_id

router = APIRouter()

# In-process registry of active streaming contexts
_active_streams: dict[str, StreamingResearchContext] = {}


class RunRequest(BaseModel):
    query: str
    tavily_api_key: str = ""


class RunResponse(BaseModel):
    session_id: str
    stream_url: str


async def _run_pipeline(
    session_id: str,
    query: str,
    ctx: StreamingResearchContext,
) -> None:
    """Execute the lead agent pipeline in the background."""
    # Import inside function to respect .env loading order (lead.py calls get_model() at import)
    from app.agents.lead import lead_agent

    try:
        result = await lead_agent.run(
            query,
            deps=ctx,
            usage_limits=UsageLimits(request_limit=20, tool_calls_limit=15),
        )
        report = result.output
        usage_data = result.usage()

        usage = UsageStats(
            requests=usage_data.requests if usage_data else 0,
            total_tokens=usage_data.total_tokens if usage_data else 0,
            request_tokens=getattr(usage_data, "request_tokens", 0) or 0,
            response_tokens=getattr(usage_data, "response_tokens", 0) or 0,
        )

        await mark_complete(
            session_id=session_id,
            report_json=report.model_dump_json(),
            events_json=json.dumps([e.model_dump(mode="json") for e in ctx.events]),
            usage_json=usage.model_dump_json(),
        )
    except Exception as exc:
        events_json = json.dumps([e.model_dump(mode="json") for e in ctx.events])
        await mark_error(session_id, str(exc), events_json)
    finally:
        # Persist any intermediate findings that were captured
        if ctx.research_findings is not None:
            await save_research_checkpoint(session_id, ctx.research_findings.model_dump_json())
        if ctx.analyst_findings is not None:
            await save_analyst_checkpoint(session_id, ctx.analyst_findings.model_dump_json())
        ctx.close_stream()
        _active_streams.pop(session_id, None)


async def _run_reporter_only(
    session_id: str,
    query: str,
    ctx: StreamingResearchContext,
) -> None:
    """Run only the reporter agent using pre-loaded findings stored in ctx."""
    from app.agents.lead import run_reporter
    from pydantic_ai.usage import Usage

    try:
        research = ctx.research_findings
        analyst = ctx.analyst_findings

        synthesis_prompt = (
            f"Research query: {query}\n\n"
            f"Market Access Findings:\n{research.model_dump_json(indent=2) if research else 'Not available'}\n\n"
            f"Analyst Findings:\n{analyst.model_dump_json(indent=2) if analyst else 'Not available'}\n\n"
            "Please synthesize the above findings into a comprehensive market report."
        )

        # Build a minimal RunContext-like object to call run_reporter tool directly
        # Instead, use reporter_agent directly
        from app.agents.reporter import reporter_agent
        from pydantic_ai import UsageLimits

        result = await reporter_agent.run(
            synthesis_prompt,
            deps=ctx,
            usage_limits=UsageLimits(request_limit=8, tool_calls_limit=0),
        )
        report = result.output
        usage_data = result.usage()

        usage = UsageStats(
            requests=usage_data.requests if usage_data else 0,
            total_tokens=usage_data.total_tokens if usage_data else 0,
            request_tokens=getattr(usage_data, "request_tokens", 0) or 0,
            response_tokens=getattr(usage_data, "response_tokens", 0) or 0,
        )

        await mark_complete(
            session_id=session_id,
            report_json=report.model_dump_json(),
            events_json=json.dumps([e.model_dump(mode="json") for e in ctx.events]),
            usage_json=usage.model_dump_json(),
        )
    except Exception as exc:
        events_json = json.dumps([e.model_dump(mode="json") for e in ctx.events])
        await mark_error(session_id, str(exc), events_json)
    finally:
        if ctx.research_findings is not None:
            await save_research_checkpoint(session_id, ctx.research_findings.model_dump_json())
        if ctx.analyst_findings is not None:
            await save_analyst_checkpoint(session_id, ctx.analyst_findings.model_dump_json())
        ctx.close_stream()
        _active_streams.pop(session_id, None)


@router.post("/run", status_code=202, response_model=RunResponse)
async def start_run(body: RunRequest) -> RunResponse:
    """Start a research pipeline run and return the session ID + SSE URL."""
    await init_db()

    session_id = generate_session_id()
    tavily_key = body.tavily_api_key or os.environ.get("TAVILY_API_KEY", "")

    ctx = StreamingResearchContext(
        tavily_api_key=tavily_key,
        db_connection=None,
        session_state=None,
    )

    await insert_session(session_id, body.query)
    _active_streams[session_id] = ctx

    # Fire and forget — runs in the event loop alongside SSE
    asyncio.create_task(_run_pipeline(session_id, body.query, ctx))

    return RunResponse(
        session_id=session_id,
        stream_url=f"/run/{session_id}/stream",
    )


async def _sse_generator(
    session_id: str,
    ctx: StreamingResearchContext,
) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted strings from the context's event queue."""
    async for event in ctx.event_generator():
        data = event.model_dump_json()
        yield f"event: workflow_event\ndata: {data}\n\n"

    # Determine final status from DB
    session = await get_session(session_id)
    status = session["status"] if session else "error"
    terminal = json.dumps({"session_id": session_id, "status": status})
    yield f"event: done\ndata: {terminal}\n\n"


@router.get("/run/{session_id}/stream")
async def stream_run(session_id: str) -> StreamingResponse:
    """SSE stream for a running pipeline. Returns 404 if session not found."""
    ctx = _active_streams.get(session_id)
    if ctx is None:
        raise HTTPException(status_code=404, detail="Stream not found or already completed")

    return StreamingResponse(
        _sse_generator(session_id, ctx),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/run/{session_id}/retry", status_code=202)
async def retry_session(session_id: str) -> dict:
    """Create a new session that resumes from checkpoints of a failed session."""
    await init_db()

    original = await get_session(session_id)
    if original is None:
        raise HTTPException(status_code=404, detail="Session not found")

    query = original["query"]
    research_json: str | None = original.get("research_json")
    analyst_json: str | None = original.get("analyst_json")
    tavily_key = os.environ.get("TAVILY_API_KEY", "")

    new_session_id = generate_session_id()

    ctx = StreamingResearchContext(
        tavily_api_key=tavily_key,
        db_connection=None,
        session_state=None,
    )

    # Pre-load any available checkpoint findings into the new context
    if research_json:
        from app.schema import MarketAccessFindings
        ctx.research_findings = MarketAccessFindings.model_validate_json(research_json)

    if analyst_json:
        from app.schema import AnalystFindings
        ctx.analyst_findings = AnalystFindings.model_validate_json(analyst_json)

    await insert_session(new_session_id, query)
    _active_streams[new_session_id] = ctx

    if research_json and analyst_json:
        # Both checkpoints exist — skip to reporter only
        asyncio.create_task(_run_reporter_only(new_session_id, query, ctx))
    else:
        # Full run (missing one or both checkpoints)
        asyncio.create_task(_run_pipeline(new_session_id, query, ctx))

    return {
        "session_id": new_session_id,
        "stream_url": f"/run/{new_session_id}/stream",
    }
