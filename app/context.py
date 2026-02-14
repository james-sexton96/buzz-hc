"""Shared dependency context for all agents."""

from dataclasses import dataclass, field
from typing import Any

from app.schema import WorkflowEvent


@dataclass
class ResearchContext:
    """Injectable context for search keys, DB connections, and session state."""

    tavily_api_key: str
    """API key for Tavily web search. Empty string if not used."""

    db_connection: Any = None
    """Optional DB connection for future use."""

    session_state: dict[str, Any] | None = None
    """Optional state accumulated during a run (e.g. findings)."""

    events: list[WorkflowEvent] = field(default_factory=list)
    """List of events captured during the research run."""

    def add_event(
        self,
        event_type: str,
        source: str,
        message: str,
        details: Any = None,
    ) -> None:
        """Add a new workflow event to the context."""
        self.events.append(
            WorkflowEvent(
                event_type=event_type,  # type: ignore
                source=source,
                message=message,
                details=details,
            )
        )
