"""Shared pytest fixtures for API tests."""

from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Redirect SQLite to a temp path for every test."""
    import api.database as db_module

    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db_module, "DB_PATH", test_db)
    # Also patch db_sessions which imports DB_PATH at call time via get_db()
    return test_db


@pytest_asyncio.fixture
async def client(temp_db):
    """AsyncClient wired to the FastAPI app with a fresh DB."""
    from api.database import init_db
    from api.main import app

    await init_db()
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
