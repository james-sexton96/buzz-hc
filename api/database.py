"""SQLite database initialization and connection management."""

import os
from pathlib import Path

import aiosqlite

DB_PATH = Path(os.environ.get("DB_PATH", "./data/sessions.db"))


async def init_db() -> None:
    """Create tables and indexes if they don't exist."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id   TEXT PRIMARY KEY,
                timestamp    TEXT NOT NULL,
                query        TEXT NOT NULL,
                status       TEXT NOT NULL DEFAULT 'running',
                report_json  TEXT,
                events_json  TEXT NOT NULL DEFAULT '[]',
                usage_json   TEXT NOT NULL DEFAULT '{}',
                error_msg    TEXT
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_timestamp
            ON sessions(timestamp DESC)
        """)
        # Idempotent migrations for new columns
        for col_def in [
            "ALTER TABLE sessions ADD COLUMN research_json TEXT",
            "ALTER TABLE sessions ADD COLUMN analyst_json TEXT",
        ]:
            try:
                await db.execute(col_def)
            except Exception:
                pass  # Column already exists
        await db.commit()


async def get_db() -> aiosqlite.Connection:
    """Open and return a database connection. Caller is responsible for closing."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db
