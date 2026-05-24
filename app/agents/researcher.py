"""Market Access Agent: FDA/EMA, clinical trials, payer/reimbursement."""

from pydantic_ai import Agent, ModelRetry, RunContext

from app.context import ResearchContext
from app.llm import get_model, get_retries
from app.schema import ClinicalTrialSummary, MarketAccessFindings
from app.tools import deep_scrape, search_clinical_trials, tavily_search

model = get_model()

researcher_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=MarketAccessFindings,
    retries=get_retries(),
    instructions=(
        "You are a Healthcare Market Access & Commercial Intelligence specialist. Your expertise "
        "spans the full market access landscape: regulatory affairs (FDA/EMA/PMDA approvals, "
        "label expansions, REMS), clinical evidence (trials, real-world evidence, HEOR), payer "
        "and reimbursement (commercial payers, Medicare/Medicaid, PBMs, formulary tiers, prior "
        "auth, step therapy, quantity limits), care delivery (site of care, administration "
        "route, specialty pharmacy, infusion channel), and access barriers (utilization "
        "management, coverage gaps, patient assistance programs).\n\n"
        "PRE-SEARCH REASONING (do this before calling any tool):\n"
        "1. What product or drug class is the question about?\n"
        "2. What is the PRIMARY research dimension? (regulatory, payer/coverage, HEOR, "
        "site-of-care, or general market access)\n"
        "3. What are the 3-4 most important information gaps to fill?\n"
        "4. Sequence your tool calls highest-priority-first.\n\n"
        "TOOL USE GUIDELINES:\n"
        "- search_clinical_trials: use for regulatory/pipeline or efficacy/safety questions. "
        "SKIP ENTIRELY if the question is purely about payer coverage, formulary, or market "
        "share with no clinical component.\n"
        "- tavily_search query 1: regulatory status OR efficacy/HEOR context (if relevant).\n"
        "- tavily_search query 2: payer/formulary landscape — target specific queries such as "
        "'[drug] formulary tier commercial payers prior authorization 2024' or '[drug class] "
        "step therapy requirements Medicare Part D'.\n"
        "- tavily_search query 3 (if budget allows): site of care, specialty pharmacy channel, "
        "REMS program details, or real-world utilization patterns.\n"
        "- deep_scrape: ONLY for specific URLs returned by search results pointing to payer "
        "medical policy pages, CMS coverage pages, FDA label/REMS pages, or specialty pharmacy "
        "hub pages. Limit to 1-2 scrapes. Do NOT scrape generic search landing pages.\n"
        "- STOP after 5-6 total tool calls. Synthesize what you have.\n\n"
        "OUTPUT FIELD GUIDANCE:\n"
        "- regulatory_snapshots: one entry per authority (FDA, EMA, etc.) with approval status, "
        "date, and indication.\n"
        "- clinical_trial_summaries: key Phase 2/3 or pivotal trials and any RWE studies.\n"
        "- payer_coverage: one PayerCoverageEntry per payer or payer segment found. If prior "
        "auth or step therapy is required, document the specific requirements. If a payer's "
        "status is unknown, set coverage_status to 'data not available' — never infer from "
        "drug price or class alone.\n"
        "- care_delivery: populate from any evidence about administration route, site of care, "
        "specialty vs retail channel, REMS requirements.\n"
        "- heor_evidence: populate from any cost-effectiveness, budget impact, or real-world "
        "outcomes studies found.\n"
        "- access_hurdles_summary: 2-3 sentence synthesis of the most significant barriers "
        "to patient access. Explicitly name what was searched for but not found.\n"
        "- reimbursement_notes: use for any payer context that doesn't fit the structured "
        "fields above.\n"
        "- raw_evidence_summary: brief summary of sources and evidence quality.\n\n"
        "ANTI-HALLUCINATION: If data for a specific payer or dimension is not found, record "
        "the absence explicitly. Never fabricate coverage tiers, PA criteria, or clinical "
        "findings. Prefer 'data not available' over an estimate."
    ),
)


@researcher_agent.output_validator
async def validate_researcher_output(
    ctx: RunContext[ResearchContext], output: MarketAccessFindings
) -> MarketAccessFindings:
    """Only reject if the output is completely empty — no data at all."""
    has_anything = (
        output.regulatory_snapshots
        or output.clinical_trial_summaries
        or output.reimbursement_notes
        or output.raw_evidence_summary
        or output.payer_coverage
        or output.care_delivery
        or output.heor_evidence
        or output.access_hurdles_summary
    )
    if not has_anything:
        raise ModelRetry(
            "Your output is completely empty. Populate at least one field with data from "
            "your research: regulatory_snapshots, clinical_trial_summaries, payer_coverage, "
            "care_delivery, heor_evidence, access_hurdles_summary, reimbursement_notes, "
            "or raw_evidence_summary."
        )
    return output


@researcher_agent.tool
async def deep_scrape_tool(
    ctx: RunContext[ResearchContext],
    url: str,
    query: str | None = None,
) -> str:
    """Scrape a specific URL and return content as Markdown. Use only for:
    - Payer medical policy pages (UnitedHealthcare, Aetna, Cigna, etc.)
    - CMS coverage database or Medicare formulary search pages
    - FDA drug label, drug approval, or REMS program pages
    - Specialty pharmacy hub or REMS enrollment pages
    Limit to 1-2 scrapes. Do not scrape generic search result landing pages — use tavily_search for those."""
    await ctx.deps.add_event("tool_call", "Crawl4AI", f"Scraping: {url}")
    res = await deep_scrape(url, query)
    await ctx.deps.add_event("tool_result", "Crawl4AI", f"Scraped {len(res)} characters")
    return res


@researcher_agent.tool
async def search_clinical_trials_tool(
    ctx: RunContext[ResearchContext],
    search_expr: str,
    max_studies: int = 50,
) -> list[ClinicalTrialSummary]:
    """Search ClinicalTrials.gov for registered studies. Use for:
    - Phase 2/3 or pivotal trials supporting efficacy/safety profile
    - Investigational drugs in the pipeline for a given indication
    - Observational or real-world evidence (RWE) studies
    - REMS-relevant safety studies or post-marketing requirements
    Skip this tool entirely if the question is purely about payer coverage, formulary access,
    market share, or prescription volume with no regulatory or clinical component.
    search_expr: drug name, condition name, or NCT ID."""
    await ctx.deps.add_event("tool_call", "ClinicalTrials", f"Searching trials for: {search_expr}")
    res = await search_clinical_trials(search_expr, max_studies=max_studies)
    await ctx.deps.add_event("tool_result", "ClinicalTrials", f"Found {len(res)} trials")
    return res


@researcher_agent.tool
async def tavily_search_tool(
    ctx: RunContext[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Broad web search for healthcare market intelligence. Use targeted queries such as:
    - Payer/formulary: "[drug] formulary tier commercial payers prior authorization 2024"
    - Step therapy: "[drug class] step therapy requirements commercial Medicare"
    - Regulatory: "[drug] FDA approval date indication label"
    - HEOR: "[drug] cost-effectiveness ICER budget impact study"
    - Site of care: "[drug] infusion center vs home infusion site of care"
    - REMS: "[drug] REMS program enrollment requirements"
    - Reimbursement: "[drug] Medicare Part D specialty tier coverage CMS"
    Returns concatenated search result summaries with source URLs."""
    return await tavily_search(ctx, query, max_results=max_results)
