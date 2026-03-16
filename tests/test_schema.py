"""Tests for Pydantic schema round-trips."""

from datetime import datetime

from app.schema import (
    AnalystFindings,
    CompetitorEntry,
    MarketAccessFindings,
    MarketReport,
    MarketSize,
    ReportSection,
    WorkflowEvent,
)


def test_workflow_event_defaults():
    event = WorkflowEvent(event_type="agent_start", source="Researcher", message="Starting")
    assert event.event_type == "agent_start"
    assert isinstance(event.timestamp, datetime)
    assert event.details is None


def test_workflow_event_roundtrip():
    event = WorkflowEvent(
        event_type="tool_call",
        source="WebSearch",
        message="Searching for GLP-1",
        details={"query": "GLP-1 market"},
    )
    dumped = event.model_dump_json()
    restored = WorkflowEvent.model_validate_json(dumped)
    assert restored.event_type == event.event_type
    assert restored.source == event.source
    assert restored.details == event.details


def test_market_report_roundtrip():
    report = MarketReport(
        title="Test Report",
        executive_summary="Summary text",
        sections=[ReportSection(heading="Market Size", content="## Details\n...")],
        sources=["https://example.com"],
        markdown_content="# Test\n",
    )
    dumped = report.model_dump_json()
    restored = MarketReport.model_validate_json(dumped)
    assert restored.title == "Test Report"
    assert len(restored.sections) == 1
    assert restored.sections[0].heading == "Market Size"


def test_analyst_findings_defaults():
    findings = AnalystFindings()
    assert findings.market_sizes == []
    assert findings.competitive_landscape == []
    assert findings.summary is None


def test_market_access_findings_roundtrip():
    findings = MarketAccessFindings(
        reimbursement_notes="Medicare covers",
        raw_evidence_summary="3 sources reviewed",
    )
    restored = MarketAccessFindings.model_validate_json(findings.model_dump_json())
    assert restored.reimbursement_notes == "Medicare covers"
