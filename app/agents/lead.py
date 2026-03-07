"""Lead Researcher (Orchestrator): plans research and delegates to specialist agents."""

from pydantic_ai import Agent, RunContext, UsageLimits

from app.agents.analyst import analyst_agent
from app.agents.reporter import reporter_agent
from app.agents.researcher import researcher_agent
from app.context import ResearchContext
from app.llm import get_model, get_retries
from app.schema import AnalystFindings, MarketAccessFindings, MarketReport

model = get_model()


lead_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=MarketReport,
    retries=get_retries(),
    instructions=(
        "You are the Lead Researcher orchestrating a pharma market research pipeline. "
        "You receive a research query and must execute exactly three tool calls in sequence:\n"
        "1. Call run_market_access_research with the query to get regulatory, clinical trial, "
        "and reimbursement findings.\n"
        "2. Call run_analyst_research with the query to get market sizing and competitive "
        "landscape data.\n"
        "3. Call run_reporter with a detailed synthesis prompt that includes the key data "
        "points from BOTH the market access and analyst findings.\n\n"
        "IMPORTANT: Call each tool exactly once. Do NOT call the same tool multiple times. "
        "Do NOT invent additional tool calls. After receiving the reporter's MarketReport, "
        "return it as your final output immediately."
    ),
)


@lead_agent.tool
async def run_market_access_research(
    ctx: RunContext[ResearchContext],
    query: str,
) -> MarketAccessFindings:
    """Delegate to the Market Access agent. Pass the research query or focus (e.g. drug/indication)."""
    ctx.deps.add_event("agent_start", "Researcher", f"Starting market access research for: {query}")
    result = await researcher_agent.run(
        f"Research market access for: {query}",
        deps=ctx.deps,
        usage=ctx.usage,
        usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8),
    )
    ctx.deps.add_event("agent_end", "Researcher", "Completed market access research")
    return result.output


@lead_agent.tool
async def run_analyst_research(
    ctx: RunContext[ResearchContext],
    query: str,
) -> AnalystFindings:
    """Delegate to the Data Analyst agent. Pass the research query or focus for market sizing and competition."""
    ctx.deps.add_event("agent_start", "Analyst", f"Starting analyst research for: {query}")
    result = await analyst_agent.run(
        f"Analyze market size and competitive landscape for: {query}",
        deps=ctx.deps,
        usage=ctx.usage,
        usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8),
    )
    ctx.deps.add_event("agent_end", "Analyst", "Completed analyst research")
    return result.output


@lead_agent.tool
async def run_reporter(
    ctx: RunContext[ResearchContext],
    synthesis_prompt: str,
) -> MarketReport:
    """Delegate to the Reporter agent. Pass a detailed prompt that includes the market access and analyst findings so it can synthesize the final report."""
    ctx.deps.add_event("agent_start", "Reporter", "Starting report synthesis")
    result = await reporter_agent.run(
        synthesis_prompt,
        deps=ctx.deps,
        usage=ctx.usage,
        usage_limits=UsageLimits(request_limit=3, tool_calls_limit=0),
    )
    ctx.deps.add_event("agent_end", "Reporter", "Completed report synthesis")
    return result.output
