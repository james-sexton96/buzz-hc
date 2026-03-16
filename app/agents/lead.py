"""Lead Researcher (Orchestrator): plans research and delegates to specialist agents."""

from typing import Union
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext, UsageLimits
from pydantic_ai.exceptions import UnexpectedModelBehavior, UsageLimitExceeded
from pydantic_ai.usage import RunUsage

from app.agents.analyst import analyst_agent
from app.agents.reporter import reporter_agent
from app.agents.researcher import researcher_agent
from app.context import ResearchContext
from app.llm import get_model, get_retries
from app.schema import AnalystFindings, MarketAccessFindings, MarketReport

model = get_model()

# Define "Limited" versions of findings to allow the workflow to continue on limit errors
class LimitedMarketAccessFindings(BaseModel):
    warning: str = Field(default="Tool call limit reached. Findings are incomplete.")
    partial_data: str = "The Market Access agent was unable to complete its full research cycle."

class LimitedAnalystFindings(BaseModel):
    warning: str = Field(default="Tool call limit reached. Analysis is incomplete.")
    partial_data: str = "The Analyst agent was unable to complete its full analysis cycle."

lead_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=MarketReport,
    retries=get_retries(),
    instructions=(
        "You are the Lead Researcher orchestrating a pharma market research pipeline. "
        "You receive a research query and must execute exactly three tool calls in sequence:\n"
        "1. Call run_market_access_research.\n"
        "2. Call run_analyst_research.\n"
        "3. Call run_reporter with a synthesis prompt.\n\n"
        "GRACEFUL ERROR HANDLING:\n"
        "If run_market_access_research or run_analyst_research returns a 'Limited' finding "
        "object, do NOT stop. Pass the warning and any partial data to the run_reporter tool. "
        "The final report should acknowledge that some data may be limited due to processing constraints.\n\n"
        "IMPORTANT: Call each tool exactly once. Do NOT call the same tool multiple times."
    ),
)


@lead_agent.tool
async def run_market_access_research(
    ctx: RunContext[ResearchContext],
    query: str,
) -> Union[MarketAccessFindings, LimitedMarketAccessFindings]:
    """Delegate to the Market Access agent."""
    ctx.deps.add_event("agent_start", "Researcher", f"Starting research for: {query}")
    
    try:
        # FIX: We pass a "fresh" usage object to prevent the child from 
        # instantly hitting the parent's tool_calls_limit.
        # We can merge the token usage back to the parent manually later if needed.
        result = await researcher_agent.run(
            f"Research market access for: {query}",
            deps=ctx.deps,
            # If you want to track total tokens, use a fresh usage object 
            # and just set the limits for this specific run.
            usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8),
        )
        
        # Manually sync token counts to the parent for global tracking
        ctx.usage.request_tokens += result.usage().request_tokens
        ctx.usage.response_tokens += result.usage().response_tokens
        
        ctx.deps.add_event("agent_end", "Researcher", "Completed research")
        ctx.deps.research_findings = result.output
        return result.output

    except (UsageLimitExceeded, Exception) as e:
        ctx.deps.add_event("agent_limit", "Researcher", f"Limit reached: {str(e)}")
        return LimitedMarketAccessFindings(
            warning=f"Market Access research hit a limit: {str(e)}"
        )

@lead_agent.tool
async def run_analyst_research(
    ctx: RunContext[ResearchContext],
    query: str,
) -> Union[AnalystFindings, LimitedAnalystFindings]:
    """Delegate to the Data Analyst agent."""
    ctx.deps.add_event("agent_start", "Analyst", f"Starting analyst research")
    
    try:
        result = await analyst_agent.run(
            f"Analyze market for: {query}",
            deps=ctx.deps,
            usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8),
        )
        
        # Sync tokens back
        ctx.usage.request_tokens += result.usage().request_tokens
        ctx.usage.response_tokens += result.usage().response_tokens

        ctx.deps.analyst_findings = result.output
        return result.output
    except (UsageLimitExceeded, Exception) as e:
        ctx.deps.add_event("agent_limit", "Analyst", f"Limit reached: {str(e)}")
        return LimitedAnalystFindings(warning=f"Analyst hit a limit: {str(e)}")

@lead_agent.tool
async def run_reporter(
    ctx: RunContext[ResearchContext],
    synthesis_prompt: str,
) -> MarketReport:
    """Delegate to the Reporter agent. Pass a detailed prompt that includes findings so it can synthesize the final report."""
    ctx.deps.add_event("agent_start", "Reporter", "Starting report synthesis")
    
    # The reporter usually has very strict limits as it's just summarizing
    result = await reporter_agent.run(
        synthesis_prompt,
        deps=ctx.deps,
        usage=ctx.usage,
        usage_limits=UsageLimits(request_limit=8, tool_calls_limit=0),
    )
    ctx.deps.add_event("agent_end", "Reporter", "Completed report synthesis")
    return result.output