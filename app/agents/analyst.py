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
        "You are a Healthcare Commercial Analytics specialist. Your expertise spans: "
        "prescription volume analysis (TRx, NBRx, patient share, market share), market "
        "sizing and forecasting, competitive landscape mapping, product launch analogue "
        "benchmarking, channel mix analysis (retail vs specialty pharmacy vs infusion "
        "center), and formulary/payer positioning of competing products.\n\n"
        "PRE-SEARCH REASONING (do this before calling any tool):\n"
        "1. What prescription or volume metric is most central to the question?\n"
        "2. Are there analogue products whose launch trajectories would be informative?\n"
        "3. Which competitive products need TRx/NBRx or market share characterization?\n"
        "4. What channel mix story exists for this drug class?\n\n"
        "TOOL USE GUIDELINES:\n"
        "- tavily_search query 1: prescription volume — e.g. 'IQVIA [drug] TRx NBRx weekly "
        "prescriptions [year]' or '[drug class] total prescription market share by product'.\n"
        "- tavily_search query 2: competitive landscape — market share by product, NBRx "
        "trends, recent market dynamics.\n"
        "- tavily_search query 3 (if budget allows): channel mix data (specialty vs retail), "
        "analogue launch ramp comparisons, or payer formulary positioning of competitors.\n"
        "- deep_scrape: ONLY for specific URLs pointing to market research data tables, drug "
        "channel blog posts with prescription data, or earnings transcripts with volume "
        "guidance. Limit to 1-2 scrapes.\n"
        "- STOP after 4-5 total tool calls. Synthesize what you have.\n\n"
        "OUTPUT FIELD GUIDANCE:\n"
        "- market_sizes: one MarketSize entry per distinct estimate found (different region, "
        "year, or methodology). Include source and methodology_notes.\n"
        "- competitive_landscape: one CompetitorEntry per product. Populate trx_weekly, "
        "nbrx_weekly, formulary_position, and channel where data exists.\n"
        "- prescription_metrics: one PrescriptionMetrics entry per distinct data point "
        "(e.g. weekly TRx for product X in Q1 2024, patient share for product Y). Tag each "
        "with time_period, product, and source.\n"
        "- analogue_launches: 1-3 comparable products if found. Entries MUST have "
        "launch_year — omit an analogue entirely rather than fabricating the year.\n"
        "- channel_mix_summary: a sentence or two on the retail/specialty/infusion split "
        "for this drug class. If unknown, say so explicitly.\n"
        "- summary: brief synthesis of key commercial insights and data gaps.\n\n"
        "ANTI-HALLUCINATION: If no specific TRx/NBRx numbers are found, leave "
        "prescription_metrics as an empty list and note the gap in channel_mix_summary. "
        "Do not estimate market share percentages without a source. Note all data gaps."
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
        or output.prescription_metrics
        or output.analogue_launches
        or output.channel_mix_summary
    )
    if not has_anything:
        raise ModelRetry(
            "Your output is completely empty. Populate at least one field with data from "
            "your research: market_sizes, competitive_landscape, prescription_metrics, "
            "analogue_launches, channel_mix_summary, or summary."
        )
    return output


@analyst_agent.tool
async def tavily_search_tool(
    ctx: RunContext[ResearchContext],
    query: str,
    max_results: int = 5,
) -> str:
    """Broad web search for commercial analytics and market data. Use targeted queries such as:
    - Rx volume: "IQVIA [drug] TRx NBRx weekly prescriptions [year]"
    - Market size: "[drug class] market size forecast [year] USD billion"
    - Competitive share: "[drug] vs [competitor] market share NBRx"
    - Analogue launches: "[comparable drug] year 1 launch TRx trajectory payer access"
    - Channel mix: "[drug] specialty pharmacy retail dispensing split percent"
    - Competitive payer positioning: "[drug class] formulary tier commercial payers comparison"
    Returns concatenated search result summaries with source URLs."""
    return await tavily_search(ctx, query, max_results=max_results)


@analyst_agent.tool
async def deep_scrape_tool(
    ctx: RunContext[ResearchContext],
    url: str,
    query: str | None = None,
) -> str:
    """Scrape a specific URL and return content as Markdown. Use only for:
    - Market research report previews or data tables (GlobalData, EvaluatePharma, etc.)
    - Drug channel blog posts or analyst pages containing prescription volume data
    - Company earnings transcript pages with specific volume or share guidance
    Limit to 1-2 scrapes. Do not scrape generic search result landing pages."""
    await ctx.deps.add_event("tool_call", "Crawl4AI", f"Scraping: {url}")
    res = await deep_scrape(url, query)
    await ctx.deps.add_event("tool_result", "Crawl4AI", f"Scraped {len(res)} characters")
    return res
