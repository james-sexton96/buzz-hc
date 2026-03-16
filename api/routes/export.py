"""GET /sessions/{id}/pdf — PDF export endpoint."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from api.database import init_db
from api.db_sessions import get_session
from app.schema import MarketReport

router = APIRouter()


@router.get("/sessions/{session_id}/pdf")
async def export_session_pdf(session_id: str) -> Response:
    """Export a completed session's report as a PDF download."""
    await init_db()
    row = await get_session(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if not row.get("report_json"):
        raise HTTPException(status_code=404, detail="Report not yet available")

    try:
        report = MarketReport.model_validate_json(row["report_json"])
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to parse report: {exc}")

    try:
        from app.export_pdf import export_pdf
        pdf_bytes = export_pdf(report)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")

    filename = f"buzz-hc-{session_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
