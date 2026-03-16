"""GET /sessions and GET /sessions/{id} endpoints."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.database import init_db
from api.db_sessions import get_session, list_sessions

router = APIRouter()


@router.get("/sessions")
async def get_sessions(
    search: str = Query(default=""),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[dict[str, Any]]:
    """List sessions newest-first with optional search and pagination."""
    await init_db()
    return await list_sessions(search=search, limit=limit, offset=offset)


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str) -> dict[str, Any]:
    """Return full session data including report and events."""
    await init_db()
    row = await get_session(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")

    result: dict[str, Any] = {
        "session_id": row["session_id"],
        "timestamp": row["timestamp"],
        "query": row["query"],
        "status": row["status"],
        "error_msg": row["error_msg"],
    }

    if row.get("report_json"):
        try:
            result["report"] = json.loads(row["report_json"])
        except Exception:
            result["report"] = None
    else:
        result["report"] = None

    if row.get("events_json"):
        try:
            result["events"] = json.loads(row["events_json"])
        except Exception:
            result["events"] = []
    else:
        result["events"] = []

    if row.get("usage_json"):
        try:
            result["usage"] = json.loads(row["usage_json"])
        except Exception:
            result["usage"] = {}
    else:
        result["usage"] = {}

    result["research_json"] = row.get("research_json")
    result["analyst_json"] = row.get("analyst_json")

    return result
