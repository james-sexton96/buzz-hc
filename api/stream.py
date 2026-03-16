"""SSE bridge: StreamingResearchContext queues events for live streaming."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, AsyncGenerator

from app.context import ResearchContext
from app.schema import WorkflowEvent

if TYPE_CHECKING:
    from app.schema import AnalystFindings, MarketAccessFindings


class StreamingResearchContext(ResearchContext):
    """ResearchContext subclass that pushes events into an asyncio Queue for SSE."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._queue: asyncio.Queue[WorkflowEvent | None] = asyncio.Queue()
        self.research_findings: MarketAccessFindings | None = None
        self.analyst_findings: AnalystFindings | None = None

    def add_event(
        self,
        event_type: str,
        source: str,
        message: str,
        details=None,
    ) -> None:
        super().add_event(event_type, source, message, details)
        # Push the newly appended event into the SSE queue
        self._queue.put_nowait(self.events[-1])

    async def event_generator(self) -> AsyncGenerator[WorkflowEvent, None]:
        """Yield WorkflowEvents as they arrive; stops on sentinel None."""
        while True:
            event = await self._queue.get()
            if event is None:
                return
            yield event

    def close_stream(self) -> None:
        """Signal the generator to stop by enqueuing a sentinel."""
        self._queue.put_nowait(None)
