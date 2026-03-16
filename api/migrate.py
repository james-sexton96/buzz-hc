"""One-time migration: JSON session files → SQLite database."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Allow running as: python -m api.migrate [reports_dir]

REPORTS_DIR = Path("./reports")


async def migrate(reports_dir: Path = REPORTS_DIR) -> None:
    from api.database import init_db
    from api.db_sessions import get_session, insert_session, mark_complete, mark_error

    await init_db()

    json_files = sorted(reports_dir.glob("*.json"), reverse=True)
    if not json_files:
        print(f"No JSON files found in {reports_dir}")
        return

    migrated = skipped = errors = 0

    for filepath in json_files:
        try:
            from app.history import load_session

            session = load_session(filepath)
        except Exception as exc:
            print(f"  SKIP {filepath.name}: could not parse — {exc}")
            errors += 1
            continue

        session_id = session.session_id

        # Skip if already in DB
        existing = await get_session(session_id)
        if existing:
            print(f"  SKIP {session_id}: already in database")
            skipped += 1
            continue

        await insert_session(session_id, session.query, session.timestamp)

        events_json = json.dumps([e.model_dump(mode="json") for e in session.events])

        if session.report:
            usage_json = session.usage.model_dump_json() if session.usage else "{}"
            await mark_complete(
                session_id=session_id,
                report_json=session.report.model_dump_json(),
                events_json=events_json,
                usage_json=usage_json,
            )
            print(f"  OK  {session_id}: migrated with report")
        else:
            await mark_error(session_id, "Migrated from JSON — no report", events_json)
            print(f"  OK  {session_id}: migrated (no report)")

        migrated += 1

    print(f"\nDone. Migrated={migrated} Skipped={skipped} Errors={errors}")


if __name__ == "__main__":
    reports_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPORTS_DIR
    asyncio.run(migrate(reports_dir))
