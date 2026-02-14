"""Data Analyst Agent: market sizing and competitive landscape."""

from pydantic_ai import Agent, RunContext

from app.context import ResearchContext
from app.llm import get_model
from app.schema import AnalystFindings
from app.tools import deep_scrape, tavily_search

model = get_model()

analyst_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=AnalystFindings,
    instructions=(
        "You are a Data Analyst specialist. Perform market sizing and competitive landscape mapping. "
        "Use tavily_search for broad market data and deep_scrape for specific report pages. "
        "Return structured AnalystFindings: market_sizes (value_usd, region, year, methodology_notes), "
        "competitive_landscape (competitor names and share/notes), and a brief summary."
    ),
)


@analyst_agent.tool
async def tavily_search_tool(
    ctx: RunContext[ResearchContext],
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
) -> str:
    """Broad web search for market data and competitor information."""
    return await tavily_search(ctx, query, max_results=max_results, search_depth=search_depth)


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
