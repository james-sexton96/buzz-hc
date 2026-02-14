"""Pydantic V2 models for agent outputs and inter-agent payloads."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class WorkflowEvent(BaseModel):
    """Event representing a step in the multi-agent workflow."""

    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: Literal["agent_start", "tool_call", "tool_result", "agent_end", "info"]
    source: str  # Agent name or Tool name
    message: str
    details: Any | None = None


class ClinicalTrialSummary(BaseModel):
    """Summary of a single clinical trial from ClinicalTrials.gov."""

    nct_id: str = Field(description="NCT identifier (e.g. NCT01234567)")
    title: str = Field(description="Study title")
    phase: str | None = Field(default=None, description="Phase (e.g. Phase 2, Phase 3)")
    status: str | None = Field(default=None, description="Overall status")
    condition: str | None = Field(default=None, description="Condition or disease")
    interventions: str | None = Field(default=None, description="Intervention summary")


class RegulatorySnapshot(BaseModel):
    """FDA/EMA regulatory status snapshot."""

    authority: str = Field(description="e.g. FDA or EMA")
    status: str | None = Field(default=None, description="Approval/regulatory status")
    approval_date: str | None = Field(default=None, description="Key approval date if known")
    indication: str | None = Field(default=None, description="Approved indication")
    notes: str | None = Field(default=None, description="Additional regulatory notes")


class MarketAccessFindings(BaseModel):
    """Structured output from the Market Access (researcher) agent."""

    regulatory_snapshots: list[RegulatorySnapshot] = Field(
        default_factory=list,
        description="FDA/EMA and other regulatory summaries",
    )
    clinical_trial_summaries: list[ClinicalTrialSummary] = Field(
        default_factory=list,
        description="Relevant clinical trial summaries",
    )
    reimbursement_notes: str | None = Field(
        default=None,
        description="Payer/reimbursement landscape notes",
    )
    raw_evidence_summary: str | None = Field(
        default=None,
        description="Brief summary of sources and evidence used",
    )


class MarketSize(BaseModel):
    """Market size result from the Data Analyst agent."""

    value_usd: float | None = Field(default=None, description="Market value in USD")
    region: str | None = Field(default=None, description="Region (e.g. US, EU, global)")
    year: str | int | None = Field(default=None, description="Year of estimate")
    methodology_notes: str | None = Field(default=None, description="How the size was derived")
    source: str | None = Field(default=None, description="Source of the estimate")


class CompetitorEntry(BaseModel):
    """Single competitor in the landscape."""

    name: str = Field(description="Competitor or product name")
    share_or_notes: str | None = Field(default=None, description="Market share or positioning notes")


class AnalystFindings(BaseModel):
    """Structured output from the Data Analyst agent."""

    market_sizes: list[MarketSize] = Field(
        default_factory=list,
        description="Market size estimates",
    )
    competitive_landscape: list[CompetitorEntry] = Field(
        default_factory=list,
        description="Competitive landscape entries",
    )
    summary: str | None = Field(default=None, description="Brief analyst summary")


class ProductAnalysis(BaseModel):
    """Per-product or per-indication analysis."""

    name: str = Field(description="Product or indication name")
    indication: str | None = Field(default=None, description="Indication or use")
    regulatory_status: str | None = Field(default=None, description="High-level regulatory status")
    reimbursement_notes: str | None = Field(default=None, description="Reimbursement notes")
    competitors: list[str] = Field(default_factory=list, description="Competitor names")


class ReportSection(BaseModel):
    """A section of the final report."""

    heading: str = Field(description="Section heading")
    content: str = Field(description="Markdown content for the section")


class MarketReport(BaseModel):
    """Top-level publication-ready market report."""

    title: str = Field(description="Report title")
    executive_summary: str = Field(description="Executive summary")
    sections: list[ReportSection] = Field(
        default_factory=list,
        description="Report sections (e.g. Market Access, Market Size, Competitive Landscape)",
    )
    sources: list[str] = Field(default_factory=list, description="Cited sources or URLs")
    markdown_content: str | None = Field(
        default=None,
        description="Full report as a single Markdown string (optional)",
    )
