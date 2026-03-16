"""Data Analyst Agent: market sizing and competitive landscape."""

from pydantic_ai import Agent, ModelRetry, RunContext

from app.context import ResearchContext
from app.llm import get_model, get_retries
from app.schema import AnalystFindings
from app.tools import deep_scrape, tavily_search

model = get_model()

analyst_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=AnalystFindings,
    retries=get_retries(),
    instructions=(
        "You are a Data Analyst specialist focused on market sizing and competitive "
        "landscape mapping for pharmaceutical products.\n\n"
        "TOOL USE GUIDELINES:\n"
        "- Use tavily_search for 2-3 targeted queries maximum (e.g. one for market size "
        "estimates, one for competitive landscape, one for market share data).\n"
        "- Use deep_scrape ONLY if you find a specific market report URL worth extracting. "
        "Limit to 1-2 scrapes maximum.\n"
        "- Do NOT repeat searches with minor query variations. Extract what you can from "
        "the results you have.\n"
        "- STOP searching after 4-5 total tool calls. Synthesize findings into structured "
        "output even if data is incomplete — note gaps in your summary.\n\n"
        "Return structured AnalystFindings: market_sizes (with value_usd, region, year, "
        "methodology_notes, source), competitive_landscape (competitor names and "
        "share/positioning notes), and a brief summary."
    ),
)


@analyst_agent.output_validator
async def validate_analyst_output(
    ctx: RunContext[ResearchContext], output: AnalystFindings
) -> AnalystFindings:
    """Only reject if the output is completely empty — no data at all."""
    has_anything = (
        output.market_sizes
        or output.competitive_landscape
        or output.summary
    )
    if not has_anything:
        raise ModelRetry(
            "Your output is completely empty. Populate at least one of: "
            "market_sizes, competitive_landscape, or summary with data from your research."
        )
    return output


@analyst_agent.tool
async def tavily_search_tool(
    ctx: RunContext[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Broad web search for market data and competitor information."""
    return await tavily_search(ctx, query, max_results=max_results)


@analyst_agent.tool
async def deep_scrape_tool(
    ctx: RunContext[ResearchContext],
    url: str,
    query: str | None = None,
) -> str:
    """Scrape a URL and return content as Markdown. Use for market report pages."""
    ctx.deps.add_event("tool_call", "Crawl4AI", f"Scraping: {url}")
    res = await deep_scrape(url, query)
    ctx.deps.add_event("tool_result", "Crawl4AI", f"Scraped {len(res)} characters")
    return res
