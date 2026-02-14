"""ClinicalTrials.gov API v2 tool: search studies and return structured summaries."""

import asyncio
import logging
from typing import Any

from app.schema import ClinicalTrialSummary

logger = logging.getLogger(__name__)

# Field names from ClinicalTrials.gov API v2 used by pytrials
_FIELDS = [
    "NCT Number",
    "Study Title",
    "Phases",
    "Study Status",
    "Conditions",
    "Interventions",
]


def _search_sync(search_expr: str, max_studies: int) -> list[dict[str, Any]]:
    """Synchronous search using pytrials. Run from thread to not block event loop."""
    from pytrials.client import ClinicalTrials

    ct = ClinicalTrials()
    raw = ct.get_study_fields(
        search_expr=search_expr,
        fields=_FIELDS,
        max_studies=min(max_studies, 1000),
        fmt="csv",
    )
    if not raw or len(raw) < 2:
        return []
    headers: list[str] = raw[0]
    rows = raw[1:]
    results = []
    for row in rows:
        if len(row) != len(headers):
            continue
        rec = dict(zip(headers, row, strict=True))
        nct = rec.get("NCT Number", "").strip() or "Unknown"
        title = rec.get("Study Title", "").strip() or "No title"
        results.append(
            ClinicalTrialSummary(
                nct_id=nct,
                title=title,
                phase=rec.get("Phases") or None,
                status=rec.get("Study Status") or None,
                condition=rec.get("Conditions") or None,
                interventions=rec.get("Interventions") or None,
            )
        )
    return results


async def search_clinical_trials(
    search_expr: str,
    max_studies: int = 50,
) -> list[ClinicalTrialSummary]:
    """
    Search ClinicalTrials.gov and return a list of trial summaries.

    Args:
        search_expr: Search expression (condition, drug name, NCT id, etc.).
        max_studies: Maximum number of studies to return (capped at 1000).

    Returns:
        List of ClinicalTrialSummary models.
    """
    try:
        return await asyncio.to_thread(_search_sync, search_expr, max_studies)
    except Exception as e:
        logger.exception("search_clinical_trials failed: %s", e)
        return []
