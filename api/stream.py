"""SSE bridge: StreamingResearchContext queues events for live streaming.

Part 4: The queue is now a *combined* queue that carries either
`WorkflowEvent` items (workflow telemetry) or `str` items (reporter token
chunks emitted by the streaming text agent). `_sse_generator` in
`api/routes/run.py` dispatches by `isinstance(item, str)`. A single
`None` sentinel terminates the stream.
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, AsyncGenerator

from app.context import ResearchContext
from app.schema import WorkflowEvent

if TYPE_CHECKING:
    from app.schema import AnalystFindings, MarketAccessFindings


# Bounded queue: at high token rates the consumer (SSE writer) might briefly
# fall behind. We drop tokens rather than blocking the producer (the reporter
# streaming LLM call) — the structured `reporter_agent` still produces the
# canonical `MarketReport`, so missing tokens degrade UX only, not correctness.
_QUEUE_MAXSIZE = 512


class StreamingResearchContext(ResearchContext):
    """ResearchContext subclass that pushes events and reporter tokens into a
    single asyncio.Queue for SSE delivery.

    Queue item types:
      - `WorkflowEvent` — workflow telemetry (existing behavior).
      - `str` — a reporter-token chunk emitted by the streaming text agent.
      - `None` — sentinel; closes the stream.
    """

    def __init__(self, *args, session_id: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        # Bounded so producers cannot OOM the process if SSE consumer stalls.
        self._queue: asyncio.Queue[WorkflowEvent | str | None] = asyncio.Queue(
            maxsize=_QUEUE_MAXSIZE,
        )
        self._session_id: str | None = session_id
        self._token_stream_closed: bool = False
        self.research_findings: MarketAccessFindings | None = None
        self.analyst_findings: AnalystFindings | None = None

    async def add_event(
        self,
        event_type: str,
        source: str,
        message: str,
        details=None,
    ) -> None:
        await super().add_event(event_type, source, message, details)
        # Push the newly appended event into the SSE queue.
        # `put_nowait` may raise QueueFull under extreme load — at that point
        # the SSE consumer is wedged anyway, so dropping the workflow event
        # is acceptable. We do NOT block here.
        try:
            self._queue.put_nowait(self.events[-1])
        except asyncio.QueueFull:
            pass
        # Persist events to DB if we have a session_id
        if self._session_id is not None:
            from api.db_sessions import update_events
            events_json = json.dumps([e.model_dump(mode="json") for e in self.events])
            await update_events(self._session_id, events_json)

    def put_token(self, chunk: str) -> None:
        """Enqueue a reporter token chunk for SSE delivery.

        Non-blocking. Drops the chunk on QueueFull (high-frequency tokens vs a
        stalled consumer should never block the LLM producer coroutine).
        Tokens are not persisted to DB (high-frequency, low replay value;
        final `markdown_content` is persisted via `mark_complete`).
        """
        if self._token_stream_closed:
            # After close_token_stream(), additional puts are silently
            # discarded — protects against stragglers from the streaming
            # agent if it raises after the finally block has fired.
            return
        try:
            self._queue.put_nowait(chunk)
        except asyncio.QueueFull:
            pass

    def close_token_stream(self) -> None:
        """Idempotent marker that the streaming text agent is done.

        Does NOT enqueue a sentinel — the overall stream sentinel is still
        `close_stream()` which is called once per run. This method exists so
        the `stream_reporter_text` helper has a clean `try/finally` symmetry
        and to harden against stragglers (see put_token).
        """
        self._token_stream_closed = True

    async def event_generator(
        self,
    ) -> AsyncGenerator[WorkflowEvent | str, None]:
        """Yield queue items as they arrive; stops on sentinel None.

        Both `WorkflowEvent` items and `str` (reporter token) items are
        yielded — the SSE generator in `api/routes/run.py` dispatches by
        isinstance check.
        """
        while True:
            item = await self._queue.get()
            if item is None:
                return
            yield item

    def close_stream(self) -> None:
        """Signal the generator to stop by enqueuing the None sentinel.

        Also marks the token stream closed so stragglers from any
        still-pending streaming-agent coroutine are silently dropped.
        """
        self._token_stream_closed = True
        # Use put_nowait with a fallback put (rare) to ensure the sentinel
        # always lands — if the queue is full, drain one item to make room.
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                self._queue.put_nowait(None)
            except asyncio.QueueFull:
                # Last-resort: leave the consumer to time out naturally.
                pass
