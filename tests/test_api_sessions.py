"""Tests for GET /sessions and GET /sessions/{id} endpoints."""

from __future__ import annotations

import json

import pytest

from api.db_sessions import insert_session, mark_complete, mark_error


async def _seed_sessions():
    """Insert sample sessions for testing."""
    await insert_session("sess_a", "GLP-1 market analysis")
    await insert_session("sess_b", "Alzheimer's FDA landscape")
    await mark_complete(
        session_id="sess_a",
        report_json=json.dumps(
            {
                "title": "GLP-1 Report",
                "executive_summary": "Strong growth",
                "sections": [],
                "sources": [],
                "markdown_content": "# GLP-1\n",
            }
        ),
        events_json=json.dumps(
            [{"event_type": "agent_start", "source": "Researcher", "message": "Start", "timestamp": "2024-01-01T00:00:00", "details": None}]
        ),
        usage_json=json.dumps({"requests": 3, "total_tokens": 1000}),
    )
    await mark_error("sess_b", "Connection timeout", "[]")


async def test_list_sessions_returns_list(client):
    await _seed_sessions()
    response = await client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


async def test_list_sessions_search(client):
    await _seed_sessions()
    response = await client.get("/sessions?search=GLP-1")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert all("GLP-1" in s["query"] for s in data)


async def test_list_sessions_pagination(client):
    await _seed_sessions()
    response_all = await client.get("/sessions?limit=10&offset=0")
    response_limited = await client.get("/sessions?limit=1&offset=0")
    assert response_all.status_code == 200
    assert response_limited.status_code == 200
    assert len(response_limited.json()) <= 1


async def test_get_session_detail_complete(client):
    await _seed_sessions()
    response = await client.get("/sessions/sess_a")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "sess_a"
    assert data["status"] == "complete"
    assert data["report"] is not None
    assert data["report"]["title"] == "GLP-1 Report"
    assert isinstance(data["events"], list)
    assert len(data["events"]) >= 1


async def test_get_session_detail_error(client):
    await _seed_sessions()
    response = await client.get("/sessions/sess_b")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["error_msg"] == "Connection timeout"
    assert data["report"] is None


async def test_get_session_not_found(client):
    response = await client.get("/sessions/does_not_exist")
    assert response.status_code == 404


async def test_get_scenarios(client):
    response = await client.get("/config/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "label" in data[0]
    assert "query" in data[0]


async def test_health_check(client):
    response = await client.get("/config/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "llm_provider" in data
    assert "llm_model" in data
