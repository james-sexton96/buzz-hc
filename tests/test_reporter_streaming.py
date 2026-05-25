"""Tests for the Part 4 reporter token streaming pipeline.

Acceptance criteria covered (from `iteration_plan.md`):

- AC1: SSE stream emits one or more `event: reporter_token` frames with payload
  `{"chunk": <string>, "token_index": <int>}` while the reporter is generating,
  followed by a terminal `event: done` frame; existing `workflow_event` frames
  continue to fire unaffected.
- AC2: Both `_run_pipeline` and `_run_reporter_only` paths emit `reporter_token`
  frames; the four-branch exception discrimination in `lead.py` is preserved.
- AC3: `MarketReport` schema extension is backward-compatible — pre-Part-4 JSON
  blobs deserialize with `country_mix is None` and `scenario_probabilities is None`.

All tests use pydantic-ai's `TestModel` so the suite runs fully offline.
Footgun: `agent.override(model=TestModel(...))` is a *sync* context manager;
`agent.run_stream(...)` is an *async* context manager. We use plain `with` for
overrides and `async with` for run_stream.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Iterator
from unittest.mock import patch

import pytest
from pydantic_ai.models.test import TestModel

from app.schema import MarketReport


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _report_args() -> dict:
    """Complete MarketReport payload for TestModel custom_output_args."""
    return {
        "title": "Streaming Test Report",
        "executive_summary": "Headline answer. Key findings. Primary caveat.",
        "sections": [
            {"heading": "Findings", "content": "Body text"},
            {"heading": "Gaps & Data Confidence", "content": "All findings present"},
            {"heading": "Key Takeaways & Implications", "content": "Bulleted insights"},
        ],
        "sources": ["https://example.com/source"],
        "markdown_content": "# Streaming Test Report\n\nBody...\n",
    }


def _parse_sse_frames(raw: str) -> list[tuple[str, str]]:
    """Parse SSE wire format into a list of (event_name, data_payload) tuples."""
    frames: list[tuple[str, str]] = []
    for block in raw.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        event_name = ""
        data_lines: list[str] = []
        for line in block.splitlines():
            if line.startswith("event: "):
                event_name = line[len("event: ") :].strip()
            elif line.startswith("data: "):
                data_lines.append(line[len("data: ") :])
        if event_name:
            frames.append((event_name, "\n".join(data_lines)))
    return frames


# ---------------------------------------------------------------------------
# AC3 — Backward-compat MarketReport deserialization
# ---------------------------------------------------------------------------


def test_market_report_backward_compat_no_country_mix():
    """AC3: a pre-Part-4 MarketReport JSON blob (lacking country_mix and
    scenario_probabilities keys) deserializes successfully with both fields
    defaulting to None — no ValidationError raised."""
    pre_part4_blob = json.dumps(
        {
            "title": "Pre-Part-4 Report",
            "executive_summary": "Summary text only.",
            "sections": [{"heading": "Section A", "content": "..."}],
            "sources": ["https://example.com"],
            "markdown_content": "# Old report\n",
            # NOTE: no country_mix or scenario_probabilities keys at all.
        }
    )

    restored = MarketReport.model_validate_json(pre_part4_blob)

    assert restored.title == "Pre-Part-4 Report"
    assert restored.country_mix is None
    assert restored.scenario_probabilities is None


def test_market_report_country_mix_roundtrip():
    """Sanity: when country_mix/scenario_probabilities are populated, they
    round-trip through JSON unchanged."""
    from app.schema import CountryMixEntry, ScenarioEntry

    report = MarketReport(
        title="With Mix",
        executive_summary="x",
        sections=[],
        sources=[],
        markdown_content="x",
        country_mix=[
            CountryMixEntry(country="DE", share_2024=20.0, share_2030=24.0, notes="growth"),
        ],
        scenario_probabilities=[
            ScenarioEntry(scenario="Base case", probability_pct=55.0, impact="neutral"),
        ],
    )
    restored = MarketReport.model_validate_json(report.model_dump_json())
    assert restored.country_mix is not None
    assert restored.country_mix[0].country == "DE"
    assert restored.scenario_probabilities is not None
    assert restored.scenario_probabilities[0].scenario == "Base case"


# ---------------------------------------------------------------------------
# AC1 — SSE stream emits reporter_token frames during the reporter phase
# ---------------------------------------------------------------------------


async def test_ac1_sse_emits_reporter_token_frames_during_reporter_phase():
    """AC1: a pipeline run emits ≥1 `reporter_token` frame with the documented
    payload shape, followed by a terminal `done` frame. Existing
    `workflow_event` frames continue to fire unaffected.
    """
    from api.routes.run import _sse_generator
    from api.stream import StreamingResearchContext
    from app.schema import WorkflowEvent

    ctx = StreamingResearchContext(
        tavily_api_key="", db_connection=None, session_state=None
    )

    # Drive the queue with a mix of workflow events and token chunks, then
    # close. This simulates what `_run_pipeline` / `_run_reporter_only` push.
    async def drive_queue() -> None:
        await ctx.add_event("agent_start", "Reporter", "Starting report synthesis")
        # Several token chunks (out of `stream_reporter_text`'s loop).
        ctx.put_token("Headline ")
        ctx.put_token("answer. ")
        ctx.put_token("Key findings.")
        await ctx.add_event("agent_end", "Reporter", "Completed")
        ctx.close_stream()

    # Patch get_session so _sse_generator can fetch a terminal status.
    async def fake_get_session(_sid: str) -> dict:
        return {"status": "complete"}

    with patch("api.routes.run.get_session", new=fake_get_session):
        # Start the driver concurrently with the SSE generator.
        drive_task = asyncio.create_task(drive_queue())
        raw_frames: list[str] = []
        async for frame in _sse_generator("sess_ac1", ctx):
            raw_frames.append(frame)
        await drive_task

    parsed = _parse_sse_frames("".join(raw_frames))
    events = [e for e, _ in parsed]

    # At least one reporter_token frame must appear.
    token_frames = [(e, d) for e, d in parsed if e == "reporter_token"]
    assert token_frames, f"Expected ≥1 reporter_token frame, got events: {events}"

    # Payload shape: {"chunk": str, "token_index": int} with index starting at 0.
    indices: list[int] = []
    for _e, data in token_frames:
        payload = json.loads(data)
        assert "chunk" in payload, "reporter_token payload must contain 'chunk'"
        assert "token_index" in payload, "reporter_token payload must contain 'token_index'"
        assert isinstance(payload["chunk"], str)
        assert isinstance(payload["token_index"], int)
        indices.append(payload["token_index"])
    assert indices[0] == 0, f"token_index should start at 0, got {indices[0]}"
    assert indices == sorted(indices), "token_index should be monotonically increasing"

    # Existing workflow_event frames still fire and are unaffected.
    workflow_frames = [(e, d) for e, d in parsed if e == "workflow_event"]
    assert workflow_frames, "Expected workflow_event frames to still fire"
    for _e, data in workflow_frames:
        we = WorkflowEvent.model_validate_json(data)
        assert we.source == "Reporter"

    # Terminal `done` frame and ordering: `done` must be last.
    assert events[-1] == "done", f"Last frame should be 'done', got {events[-1]}"
    assert events.count("done") == 1, "Exactly one 'done' frame expected"


# ---------------------------------------------------------------------------
# AC1/AC2 — stream_reporter_text helper emits chunks into the SSE queue
# ---------------------------------------------------------------------------


async def test_stream_reporter_text_enqueues_tokens_and_closes():
    """The streaming helper places chunks on the ctx queue and idempotently
    closes the token stream in `finally`.

    Uses pydantic-ai's TestModel with `custom_output_text` — note that
    `agent.override()` is a *sync* context manager (plain `with`), while
    `agent.run_stream()` is *async* (handled internally by the helper).
    """
    from api.stream import StreamingResearchContext
    from app.agents.reporter import _reporter_stream_agent, stream_reporter_text

    ctx = StreamingResearchContext(
        tavily_api_key="", db_connection=None, session_state=None
    )

    with _reporter_stream_agent.override(
        model=TestModel(custom_output_text="Hello streaming world")
    ):
        accumulated = await stream_reporter_text("synthesis prompt", ctx)

    assert accumulated, "stream_reporter_text should return accumulated text"

    # Drain the queue and confirm at least one `str` chunk was enqueued.
    collected: list[object] = []
    while True:
        try:
            collected.append(ctx._queue.get_nowait())
        except asyncio.QueueEmpty:
            break

    string_items = [c for c in collected if isinstance(c, str)]
    assert string_items, f"Expected at least one str chunk in queue, got {collected}"
    # Concatenated chunks should reproduce the test model's full output.
    assert "".join(string_items) == "Hello streaming world"

    # Token stream marked closed; further put_token calls are silently dropped.
    assert ctx._token_stream_closed is True
    ctx.put_token("post-close should be ignored")
    # Queue size remains unchanged after a post-close put_token.
    assert ctx._queue.qsize() == 0


# ---------------------------------------------------------------------------
# AC2 — _run_reporter_only retry path also emits reporter_token frames
# ---------------------------------------------------------------------------


async def test_ac2_run_reporter_only_emits_reporter_token_frames(client):
    """AC2 retry path: `_run_reporter_only` streams tokens before running the
    structured `reporter_agent`. We capture the queue contents after the
    background task completes and assert at least one `str` chunk appeared.
    """
    from api.db_sessions import (
        insert_session,
        mark_error,
        save_analyst_checkpoint,
        save_research_checkpoint,
    )
    from api.routes import run as run_module
    from api.stream import StreamingResearchContext
    from app.agents.reporter import _reporter_stream_agent, reporter_agent
    from app.schema import AnalystFindings, MarketAccessFindings

    # Seed a failed session with both checkpoints so the retry route
    # dispatches to _run_reporter_only.
    await insert_session("sess_retry_stream", "retry query")
    await save_research_checkpoint(
        "sess_retry_stream",
        MarketAccessFindings(raw_evidence_summary="prior research").model_dump_json(),
    )
    await save_analyst_checkpoint(
        "sess_retry_stream",
        AnalystFindings(summary="prior analyst").model_dump_json(),
    )
    await mark_error("sess_retry_stream", "earlier failure", "[]", failed_stage="pipeline")

    captured_ctx: dict[str, StreamingResearchContext] = {}

    # Patch _run_reporter_only with a thin wrapper that pre-registers the ctx
    # under TestModel overrides, then awaits the real function.
    real_reporter_only = run_module._run_reporter_only

    async def wrapped_reporter_only(session_id: str, query: str, ctx: StreamingResearchContext) -> None:
        captured_ctx["ctx"] = ctx
        # Drain the queue concurrently with the work so we capture token
        # frames before close_stream removes them.
        drained: list[object] = []

        async def drain() -> None:
            while True:
                try:
                    item = await asyncio.wait_for(ctx._queue.get(), timeout=5.0)
                except asyncio.TimeoutError:
                    return
                drained.append(item)
                if item is None:
                    return

        drain_task = asyncio.create_task(drain())
        try:
            with _reporter_stream_agent.override(
                model=TestModel(custom_output_text="Streaming retry draft text")
            ):
                with reporter_agent.override(
                    model=TestModel(call_tools=[], custom_output_args=_report_args())
                ):
                    await real_reporter_only(session_id, query, ctx)
        finally:
            await drain_task
        captured_ctx["drained"] = drained  # type: ignore[assignment]

    with patch.object(run_module, "_run_reporter_only", new=wrapped_reporter_only):
        response = await client.post("/run/sess_retry_stream/retry")
        assert response.status_code == 202
        # Allow the background task to complete.
        for _ in range(100):
            if "drained" in captured_ctx:
                break
            await asyncio.sleep(0.02)

    assert "drained" in captured_ctx, "Background _run_reporter_only never completed"
    drained = captured_ctx["drained"]
    string_items = [c for c in drained if isinstance(c, str)]
    assert string_items, (
        "Retry path should emit at least one reporter token chunk into the queue; "
        f"drained items: {drained}"
    )


# ---------------------------------------------------------------------------
# AC2 — Four-branch exception discrimination structurally preserved
# ---------------------------------------------------------------------------


def test_ac2_four_branch_exception_discrimination_preserved():
    """AC2: the four-branch exception discrimination remains in `lead.py`
    `run_reporter` (TimeoutError / UnexpectedModelBehavior / UsageLimitExceeded
    / generic Exception). This is a source-level grep — if the branches are
    renamed or merged, the test must be updated atomically.
    """
    import pathlib

    lead_src = pathlib.Path(__file__).parent.parent / "app" / "agents" / "lead.py"
    src = lead_src.read_text()

    # Slice the `run_reporter` function body: from the `async def run_reporter`
    # line through the end of the file (or the next top-level def). The body
    # spans multiple blank lines internally, so we can't terminate on \n\n.
    m = re.search(
        r"async def run_reporter\(.*?(?=\n(?:async )?def |\Z)",
        src,
        flags=re.DOTALL,
    )
    assert m, "run_reporter not found in app/agents/lead.py"
    body = m.group(0)

    # All four discriminated exception classes must appear in `run_reporter`.
    assert "asyncio.TimeoutError" in body or "TimeoutError" in body
    assert "UsageLimitExceeded" in body
    assert "UnexpectedModelBehavior" in body
    # The fallback `Exception` handler is on the combined except clause.
    assert "Exception" in body
