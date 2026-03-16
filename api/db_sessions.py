"""CRUD operations for the sessions table."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import aiosqlite

from api.database import get_db


async def insert_session(
    session_id: str,
    query: str,
    timestamp: datetime | None = None,
) -> None:
    """Insert a new session row with status='running'."""
    ts = (timestamp or datetime.now()).isoformat()
    db = await get_db()
    try:
        await db.execute(
            """
            INSERT INTO sessions (session_id, timestamp, query, status, events_json, usage_json)
            VALUES (?, ?, ?, 'running', '[]', '{}')
            """,
            (session_id, ts, query),
        )
        await db.commit()
    finally:
        await db.close()


async def mark_complete(
    session_id: str,
    report_json: str,
    events_json: str,
    usage_json: str,
) -> None:
    """Update session to status='complete' with final data."""
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE sessions
            SET status='complete', report_json=?, events_json=?, usage_json=?
            WHERE session_id=?
            """,
            (report_json, events_json, usage_json, session_id),
        )
        await db.commit()
    finally:
        await db.close()


async def mark_error(session_id: str, error_msg: str, events_json: str) -> None:
    """Update session to status='error'."""
    db = await get_db()
    try:
        await db.execute(
            """
            UPDATE sessions
            SET status='error', error_msg=?, events_json=?
            WHERE session_id=?
            """,
            (error_msg, events_json, session_id),
        )
        await db.commit()
    finally:
        await db.close()


async def get_session(session_id: str) -> dict[str, Any] | None:
    """Return a single session row as a dict, or None if not found."""
    db = await get_db()
    try:
        async with db.execute(
            "SELECT * FROM sessions WHERE session_id=?", (session_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row is None:
                return None
            return dict(row)
    finally:
        await db.close()


async def list_sessions(
    search: str = "",
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """List sessions newest-first with optional search filter."""
    db = await get_db()
    try:
        if search:
            pattern = f"%{search}%"
            async with db.execute(
                """
                SELECT session_id, timestamp, query, status, error_msg
                FROM sessions
                WHERE query LIKE ?
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (pattern, limit, offset),
            ) as cursor:
                rows = await cursor.fetchall()
        else:
            async with db.execute(
                """
                SELECT session_id, timestamp, query, status, error_msg
                FROM sessions
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ) as cursor:
                rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await db.close()


async def save_research_checkpoint(session_id: str, research_json: str) -> None:
    """Persist MarketAccessFindings JSON for a running session."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE sessions SET research_json=? WHERE session_id=?",
            (research_json, session_id),
        )
        await db.commit()
    finally:
        await db.close()


async def save_analyst_checkpoint(session_id: str, analyst_json: str) -> None:
    """Persist AnalystFindings JSON for a running session."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE sessions SET analyst_json=? WHERE session_id=?",
            (analyst_json, session_id),
        )
        await db.commit()
    finally:
        await db.close()


async def update_events(session_id: str, events_json: str) -> None:
    """Update the events_json column for a running session."""
    db = await get_db()
    try:
        await db.execute(
            "UPDATE sessions SET events_json=? WHERE session_id=?",
            (events_json, session_id),
        )
        await db.commit()
    finally:
        await db.close()
