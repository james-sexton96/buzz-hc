"""Persistence layer for research sessions — save/load as local JSON files."""

import random
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from app.schema import AnalystFindings, MarketAccessFindings, MarketReport, WorkflowEvent

# Default directory for saved sessions
DEFAULT_HISTORY_DIR = Path("./reports")


class UsageStats(BaseModel):
    """Token and request usage stats from a research run."""

    requests: int = 0
    total_tokens: int = 0
    request_tokens: int = 0
    response_tokens: int = 0


class ResearchSession(BaseModel):
    """A complete research session, serializable to JSON."""

    session_id: str = Field(description="Unique session identifier (timestamp-based)")
    timestamp: datetime = Field(default_factory=datetime.now)
    query: str = Field(description="The original research query")
    report: MarketReport | None = Field(default=None, description="The final report")
    events: list[WorkflowEvent] = Field(
        default_factory=list, description="Workflow trace events"
    )
    usage: UsageStats = Field(default_factory=UsageStats)


class CheckpointSession(BaseModel):
    """A partial research session saved mid-run so it can be resumed later."""

    session_id: str = Field(description="Unique session identifier (same as the failed run)")
    timestamp: datetime = Field(default_factory=datetime.now)
    query: str = Field(description="The original research query")
    research_findings: MarketAccessFindings | None = Field(
        default=None, description="Researcher agent output (if completed before failure)"
    )
    analyst_findings: AnalystFindings | None = Field(
        default=None, description="Analyst agent output (if completed before failure)"
    )
    events: list[WorkflowEvent] = Field(
        default_factory=list, description="Workflow events captured before failure"
    )
    stage_reached: str = Field(
        default="none",
        description="Furthest stage completed: 'none' | 'research' | 'analyst'",
    )
    failure_reason: str | None = Field(
        default=None, description="Exception message or 'KeyboardInterrupt'"
    )


def _ensure_dir(directory: Path) -> Path:
    """Create the history directory if it doesn't exist."""
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def generate_session_id() -> str:
    """Generate a unique session ID from timestamp + random suffix."""
    suffix = random.randint(0, 0xFFFF)
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{suffix:04x}"


def save_session(
    session: ResearchSession,
    directory: Path = DEFAULT_HISTORY_DIR,
) -> Path:
    """Save a research session to a JSON file. Returns the file path."""
    _ensure_dir(directory)
    filename = f"{session.session_id}.json"
    filepath = directory / filename
    filepath.write_text(session.model_dump_json(indent=2))
    return filepath


def load_session(filepath: Path) -> ResearchSession:
    """Load a research session from a JSON file."""
    data = filepath.read_text()
    return ResearchSession.model_validate_json(data)


DEFAULT_CHECKPOINT_DIR = Path("./reports/checkpoints")


def save_checkpoint(
    checkpoint: CheckpointSession,
    directory: Path = DEFAULT_CHECKPOINT_DIR,
) -> Path:
    """Save a mid-run checkpoint to JSON. Returns the file path."""
    _ensure_dir(directory)
    filepath = directory / f"{checkpoint.session_id}.checkpoint.json"
    filepath.write_text(checkpoint.model_dump_json(indent=2))
    return filepath


def load_checkpoint(
    session_id_or_path: str,
    directory: Path = DEFAULT_CHECKPOINT_DIR,
) -> "CheckpointSession":
    """Load a checkpoint by session ID or absolute/relative file path."""
    p = Path(session_id_or_path)
    filepath = p if p.exists() else directory / f"{session_id_or_path}.checkpoint.json"
    if not filepath.exists():
        raise FileNotFoundError(
            f"No checkpoint found at {filepath}. "
            f"Checkpoints are stored in {directory}/"
        )
    return CheckpointSession.model_validate_json(filepath.read_text())


def list_sessions(directory: Path = DEFAULT_HISTORY_DIR) -> list[dict[str, Any]]:
    """List all saved sessions with basic metadata.

    Returns a list of dicts sorted by filename descending (newest first).
    Each dict contains: session_id, timestamp, query (preview), filepath,
    has_report.
    """
    if not directory.is_dir():
        return []

    sessions: list[dict[str, Any]] = []
    for f in sorted(directory.glob("*.json"), reverse=True):
        try:
            session = load_session(f)
            query_preview = (
                session.query[:80] + "…"
                if len(session.query) > 80
                else session.query
            )
            sessions.append(
                {
                    "session_id": session.session_id,
                    "timestamp": session.timestamp.strftime("%Y-%m-%d %H:%M"),
                    "query": query_preview,
                    "filepath": str(f),
                    "has_report": session.report is not None,
                }
            )
        except Exception:
            # Skip corrupt or unreadable files
            continue

    return sessions
