"""Tests for SQLite CRUD operations in api/db_sessions.py."""

from __future__ import annotations

import pytest

from api.database import init_db
from api.db_sessions import (
    get_session,
    insert_session,
    list_sessions,
    mark_complete,
    mark_error,
)


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


async def test_insert_and_get_session():
    await insert_session("sess_001", "What is GLP-1?")
    row = await get_session("sess_001")
    assert row is not None
    assert row["session_id"] == "sess_001"
    assert row["query"] == "What is GLP-1?"
    assert row["status"] == "running"


async def test_get_session_not_found():
    result = await get_session("nonexistent_id")
    assert result is None


async def test_mark_complete():
    await insert_session("sess_002", "Alzheimer's treatments")
    await mark_complete(
        session_id="sess_002",
        report_json='{"title": "Test Report", "executive_summary": "Summary"}',
        events_json="[]",
        usage_json='{"requests": 5}',
    )
    row = await get_session("sess_002")
    assert row["status"] == "complete"
    assert row["report_json"] is not None
    assert "Test Report" in row["report_json"]


async def test_mark_error():
    await insert_session("sess_003", "Failed query")
    await mark_error("sess_003", "LLM timeout", "[]")
    row = await get_session("sess_003")
    assert row["status"] == "error"
    assert row["error_msg"] == "LLM timeout"


async def test_list_sessions_empty():
    rows = await list_sessions()
    assert isinstance(rows, list)


async def test_list_sessions_with_data():
    await insert_session("sess_list_1", "Query one")
    await insert_session("sess_list_2", "Query two")
    rows = await list_sessions()
    ids = [r["session_id"] for r in rows]
    assert "sess_list_1" in ids
    assert "sess_list_2" in ids


async def test_list_sessions_search():
    await insert_session("sess_search_1", "GLP-1 market size")
    await insert_session("sess_search_2", "Alzheimer's landscape")
    rows = await list_sessions(search="GLP-1")
    assert len(rows) >= 1
    assert all("GLP-1" in r["query"] for r in rows)


async def test_list_sessions_pagination():
    for i in range(5):
        await insert_session(f"sess_page_{i}", f"Query {i}")
    page1 = await list_sessions(limit=3, offset=0)
    page2 = await list_sessions(limit=3, offset=3)
    assert len(page1) <= 3
    # Ensure no overlap
    ids1 = {r["session_id"] for r in page1}
    ids2 = {r["session_id"] for r in page2}
    assert ids1.isdisjoint(ids2)
