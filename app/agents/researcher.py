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
        "You are a Market Access specialist. Research FDA/EMA regulatory status, "
        "clinical trial status (use search_clinical_trials), and payer/reimbursement landscape. "
        "Use deep_scrape for JS-heavy pharma/regulatory portals and tavily_search for broad search. "
        "Return structured MarketAccessFindings: regulatory_snapshots, clinical_trial_summaries, "
        "reimbursement_notes, and a brief raw_evidence_summary."
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
    )
    if not has_anything:
        raise ModelRetry(
            "Your output is completely empty. Populate at least one of: "
            "regulatory_snapshots, clinical_trial_summaries, reimbursement_notes, "
            "or raw_evidence_summary with data from your research."
        )
    return output


@researcher_agent.tool
async def deep_scrape_tool(
    ctx: RunContext[ResearchContext],
    url: str,
    query: str | None = None,
) -> str:
    """Scrape a URL and return content as Markdown. Use for pharma/regulatory portals."""
    ctx.deps.add_event("tool_call", "Crawl4AI", f"Scraping: {url}")
    res = await deep_scrape(url, query)
    ctx.deps.add_event("tool_result", "Crawl4AI", f"Scraped {len(res)} characters")
    return res


@researcher_agent.tool
async def search_clinical_trials_tool(
    ctx: RunContext[ResearchContext],
    search_expr: str,
    max_studies: int = 50,
) -> list[ClinicalTrialSummary]:
    """Search ClinicalTrials.gov. search_expr can be condition, drug name, or NCT id."""
    ctx.deps.add_event("tool_call", "ClinicalTrials", f"Searching trials for: {search_expr}")
    res = await search_clinical_trials(search_expr, max_studies=max_studies)
    ctx.deps.add_event("tool_result", "ClinicalTrials", f"Found {len(res)} trials")
    return res


@researcher_agent.tool
async def tavily_search_tool(
    ctx: RunContext[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Broad web search. Use for regulatory, reimbursement, and market access topics."""
    return await tavily_search(ctx, query, max_results=max_results)
