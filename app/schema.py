"""Pydantic V2 models for agent outputs and inter-agent payloads."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Healthcare market access — payer, care delivery, HEOR
# ---------------------------------------------------------------------------


class PayerCoverageEntry(BaseModel):
    """Coverage status for a single payer or payer segment."""

    payer_name: str = Field(description="Payer name, e.g. 'UnitedHealthcare', 'CVS Caremark', 'Medicare Part D'")
    coverage_status: str | None = Field(default=None, description="'covered', 'not covered', 'restricted', 'PA required', or 'data not available'")
    formulary_tier: str | None = Field(default=None, description="e.g. 'Tier 1', 'Tier 2', 'Specialty', 'Non-formulary'")
    prior_auth_required: bool | None = Field(default=None, description="Whether prior authorization is required")
    step_therapy_required: bool | None = Field(default=None, description="Whether step therapy is required")
    step_therapy_details: str | None = Field(default=None, description="Which agents must fail first, or other step-edit conditions")
    notes: str | None = Field(default=None, description="Any additional access conditions or restrictions")


class HEORSummary(BaseModel):
    """Health economics and outcomes research evidence summary."""

    study_type: str | None = Field(default=None, description="e.g. 'cost-effectiveness', 'budget impact', 'real-world evidence', 'observational'")
    headline_finding: str | None = Field(default=None, description="Key result or conclusion of the study")
    source: str | None = Field(default=None, description="Source URL or publication reference")


class CareDeliveryProfile(BaseModel):
    """Site of care and channel characterization for a product."""

    primary_site_of_care: str | None = Field(default=None, description="e.g. 'infusion center', 'home infusion', 'physician office', 'retail pharmacy'")
    administration_route: str | None = Field(default=None, description="e.g. 'IV', 'SC', 'oral', 'IM'")
    specialty_pharmacy_required: bool | None = Field(default=None, description="Whether the product must be dispensed through a specialty pharmacy")
    home_infusion_eligible: bool | None = Field(default=None, description="Whether home infusion is a supported care setting")
    rems_program: bool | None = Field(default=None, description="Whether a REMS program is in place")
    rems_details: str | None = Field(default=None, description="Key REMS requirements or restrictions")
    channel_mix_notes: str | None = Field(default=None, description="e.g. '~60% specialty pharmacy, ~40% retail'")


# ---------------------------------------------------------------------------
# Commercial analytics — prescription volume and launch analogues
# ---------------------------------------------------------------------------


class PrescriptionMetrics(BaseModel):
    """A single prescription volume or share data point."""

    metric_type: str = Field(description="'TRx', 'NBRx', 'patient share', 'market share', or similar")
    value: float | None = Field(default=None, description="Numeric value")
    unit: str | None = Field(default=None, description="e.g. 'scripts/week', '% share', 'patients/month'")
    time_period: str | None = Field(default=None, description="e.g. 'Q1 2024', 'Week 52 post-launch', 'Full Year 2023'")
    product: str | None = Field(default=None, description="Product or drug name this metric applies to")
    source: str | None = Field(default=None, description="Source of the data (IQVIA, SYMPHONY, company filing, etc.)")
    notes: str | None = Field(default=None, description="Context or caveats for this data point")


class AnalogueLaunch(BaseModel):
    """Launch trajectory for a comparable product used as a benchmark."""

    product_name: str = Field(description="Analogue product name")
    indication: str | None = Field(default=None, description="Approved indication")
    launch_year: int | None = Field(default=None, description="Year of US launch")
    year1_trx: float | None = Field(default=None, description="Approximate total Rx in Year 1 post-launch")
    peak_share_pct: float | None = Field(default=None, description="Peak market share percentage achieved")
    payer_access_at_launch: str | None = Field(default=None, description="Payer/formulary access context at time of launch")
    key_lessons: str | None = Field(default=None, description="Commercially relevant lessons from this analogue")


# ---------------------------------------------------------------------------
# Workflow events
# ---------------------------------------------------------------------------


class WorkflowEvent(BaseModel):
    """Event representing a step in the multi-agent workflow."""

    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: Literal["agent_start", "tool_call", "tool_result", "agent_end", "info", "agent_limit"]
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
        description="Payer/reimbursement landscape notes (legacy free-text field)",
    )
    raw_evidence_summary: str | None = Field(
        default=None,
        description="Brief summary of sources and evidence used",
    )
    payer_coverage: list[PayerCoverageEntry] = Field(
        default_factory=list,
        description="Per-payer coverage status, formulary tier, and access conditions",
    )
    care_delivery: CareDeliveryProfile | None = Field(
        default=None,
        description="Site of care, administration route, specialty pharmacy, and REMS profile",
    )
    heor_evidence: list[HEORSummary] = Field(
        default_factory=list,
        description="Health economics and outcomes research evidence",
    )
    access_hurdles_summary: str | None = Field(
        default=None,
        description="2-3 sentence synthesis of the biggest barriers to patient access",
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
    trx_weekly: float | None = Field(default=None, description="Approximate weekly TRx volume if available")
    nbrx_weekly: float | None = Field(default=None, description="Approximate weekly NBRx volume if available")
    formulary_position: str | None = Field(default=None, description="Typical formulary tier or access status")
    channel: str | None = Field(default=None, description="Primary dispensing channel, e.g. 'specialty pharmacy', 'retail', 'buy-and-bill'")


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
    prescription_metrics: list[PrescriptionMetrics] = Field(
        default_factory=list,
        description="TRx, NBRx, patient share, and other prescription volume data points",
    )
    analogue_launches: list[AnalogueLaunch] = Field(
        default_factory=list,
        description="Comparable product launches used as benchmarks",
    )
    channel_mix_summary: str | None = Field(
        default=None,
        description="Summary of retail vs specialty pharmacy vs infusion channel split",
    )


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
