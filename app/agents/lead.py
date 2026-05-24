"""Lead Researcher (Orchestrator): plans research and delegates to specialist agents."""

import asyncio
import os
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

# Timeout (seconds) for each sub-agent call — configurable via AGENT_TIMEOUT env var.
# Ollama on M1 can take 90-180s; default 120s bounds worst-case hangs.
_AGENT_TIMEOUT = float(os.environ.get("AGENT_TIMEOUT", "120"))

# Number of additional retry attempts on UnexpectedModelBehavior per stage.
# Default 2 means: initial attempt + up to 2 retries = 3 total attempts.
# Configurable via STAGE_RETRIES env var.
_STAGE_RETRIES = int(os.environ.get("STAGE_RETRIES", "2"))


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
        "You are the orchestrator of a healthcare market intelligence pipeline. Your "
        "outputs serve pharmaceutical commercial teams, market access leads, and payer "
        "strategy professionals.\n\n"
        "You receive a research query and must execute exactly three tool calls in sequence:\n"
        "1. Call run_market_access_research.\n"
        "2. Call run_analyst_research.\n"
        "3. Call run_reporter with a detailed synthesis prompt.\n\n"
        "PRE-TOOL REASONING (before calling any tool, reason through these steps):\n"
        "A. QUESTION ARCHETYPE — classify the question as one of:\n"
        "   - 'coverage/formulary': focuses on payer coverage, formulary tier, prior auth, "
        "step therapy, or market basket access\n"
        "   - 'volume/prescribing': focuses on TRx, NBRx, patient share, or prescription "
        "trends for a product or class\n"
        "   - 'care-delivery': focuses on site of care, administration route, specialty "
        "pharmacy, home infusion, or REMS\n"
        "   - 'regulatory/pipeline': focuses on FDA/EMA approval status, clinical trials, "
        "or pipeline development\n"
        "   - 'market-sizing/competitive': focuses on market size, revenue forecasts, or "
        "competitive landscape and market share\n"
        "   - 'multi-dimensional': spans two or more of the above dimensions\n"
        "B. KEY PRODUCT/DRUG CLASS — identify the primary product(s) or drug class.\n"
        "C. PRIMARY DIMENSIONS — identify 2-3 specific information areas most central to "
        "answering the question (e.g. 'payer coverage, step therapy, formulary tier').\n\n"
        "TOOL CALL CONSTRUCTION:\n"
        "Pass structured briefings to each sub-agent — not just the raw query. The "
        "query argument you send to run_market_access_research should include:\n"
        "  QUESTION: [original query]\n"
        "  QUESTION TYPE: [archetype]\n"
        "  KEY PRODUCT/DRUG CLASS: [extracted]\n"
        "  PRIMARY DIMENSIONS: [dimensions]\n"
        "Similarly for run_analyst_research.\n\n"
        "SYNTHESIS PROMPT CONSTRUCTION:\n"
        "The synthesis_prompt you pass to run_reporter must include:\n"
        "  RESEARCH QUESTION: [original query]\n"
        "  QUESTION ARCHETYPE: [archetype you identified]\n"
        "  PRIMARY RESEARCH DIMENSIONS: [dimensions]\n"
        "  MARKET ACCESS FINDINGS (from Researcher Agent):\n[JSON of findings]\n"
        "  ANALYST FINDINGS (from Analyst Agent):\n[JSON of findings]\n"
        "  REPORTER INSTRUCTIONS: [the standard instructions block below]\n\n"
        "Standard reporter instructions block:\n"
        "1. Use QUESTION ARCHETYPE to select the appropriate section structure.\n"
        "2. Every section must draw only from the findings above — no external facts.\n"
        "3. For any null, empty, or 'data not available' field, note it in Gaps & Data Confidence.\n"
        "4. The 'Gaps & Data Confidence' section is MANDATORY in every report.\n"
        "5. Populate sources with every URL present in the findings.\n"
        "6. Executive summary: paragraph 1 = headline answer, paragraph 2 = key commercial "
        "findings, paragraph 3 = primary caveat or risk.\n"
        "7. Populate markdown_content with the complete formatted report.\n\n"
        "GRACEFUL ERROR HANDLING:\n"
        "If run_market_access_research or run_analyst_research returns a 'Limited' finding "
        "object, do NOT stop. Pass the warning and partial data to run_reporter. The final "
        "report should acknowledge that some data may be limited.\n\n"
        "IMPORTANT: Call each tool exactly once. Do NOT call the same tool multiple times."
    ),
)


@lead_agent.tool
async def run_market_access_research(
    ctx: RunContext[ResearchContext],
    query: str,
) -> Union[MarketAccessFindings, LimitedMarketAccessFindings]:
    """Delegate to the Market Access agent.

    Retries on UnexpectedModelBehavior up to _STAGE_RETRIES additional attempts.
    Other failure modes (TimeoutError, UsageLimitExceeded, generic Exception)
    are NOT retried and return a LimitedMarketAccessFindings fallback.
    """
    await ctx.deps.add_event("agent_start", "Researcher", f"Starting research for: {query}")

    last_unexpected: UnexpectedModelBehavior | None = None
    for attempt in range(_STAGE_RETRIES + 1):
        try:
            result = await asyncio.wait_for(
                researcher_agent.run(
                    f"Research market access for: {query}",
                    deps=ctx.deps,
                    usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8),
                ),
                timeout=_AGENT_TIMEOUT,
            )

            ctx.usage.request_tokens += result.usage().request_tokens
            ctx.usage.response_tokens += result.usage().response_tokens

            await ctx.deps.add_event("agent_end", "Researcher", "Completed research")
            ctx.deps.research_findings = result.output
            return result.output

        except asyncio.TimeoutError:
            await ctx.deps.add_event("agent_limit", "Researcher", f"Timeout after {_AGENT_TIMEOUT}s")
            return LimitedMarketAccessFindings(
                warning=f"Market Access research timed out after {_AGENT_TIMEOUT}s"
            )
        except UnexpectedModelBehavior as e:
            last_unexpected = e
            if attempt < _STAGE_RETRIES:
                await ctx.deps.add_event(
                    "info",
                    "Researcher",
                    f"Retry {attempt + 1}/{_STAGE_RETRIES}: {e}",
                )
                continue
            await ctx.deps.add_event(
                "agent_limit",
                "Researcher",
                f"Limit reached: {str(e)}",
            )
            return LimitedMarketAccessFindings(
                warning=f"Market Access research hit a limit: {str(e)}"
            )
        except UsageLimitExceeded as e:
            await ctx.deps.add_event("agent_limit", "Researcher", f"Limit reached: {str(e)}")
            return LimitedMarketAccessFindings(
                warning=f"Market Access research hit a limit: {str(e)}"
            )
        except Exception as e:
            await ctx.deps.add_event("agent_limit", "Researcher", f"Limit reached: {str(e)}")
            return LimitedMarketAccessFindings(
                warning=f"Market Access research hit a limit: {str(e)}"
            )

    # Defensive fallback — should not be reachable because the final
    # UnexpectedModelBehavior attempt returns inside the loop.
    return LimitedMarketAccessFindings(
        warning=f"Market Access research hit a limit: {last_unexpected}"
    )


@lead_agent.tool
async def run_analyst_research(
    ctx: RunContext[ResearchContext],
    query: str,
) -> Union[AnalystFindings, LimitedAnalystFindings]:
    """Delegate to the Data Analyst agent.

    Retries on UnexpectedModelBehavior up to _STAGE_RETRIES additional attempts.
    Other failure modes (TimeoutError, UsageLimitExceeded, generic Exception)
    are NOT retried and return a LimitedAnalystFindings fallback.
    """
    await ctx.deps.add_event("agent_start", "Analyst", "Starting analyst research")

    last_unexpected: UnexpectedModelBehavior | None = None
    for attempt in range(_STAGE_RETRIES + 1):
        try:
            result = await asyncio.wait_for(
                analyst_agent.run(
                    f"Analyze market for: {query}",
                    deps=ctx.deps,
                    usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8),
                ),
                timeout=_AGENT_TIMEOUT,
            )

            ctx.usage.request_tokens += result.usage().request_tokens
            ctx.usage.response_tokens += result.usage().response_tokens

            ctx.deps.analyst_findings = result.output
            return result.output

        except asyncio.TimeoutError:
            await ctx.deps.add_event("agent_limit", "Analyst", f"Timeout after {_AGENT_TIMEOUT}s")
            return LimitedAnalystFindings(
                warning=f"Analyst timed out after {_AGENT_TIMEOUT}s"
            )
        except UnexpectedModelBehavior as e:
            last_unexpected = e
            if attempt < _STAGE_RETRIES:
                await ctx.deps.add_event(
                    "info",
                    "Analyst",
                    f"Retry {attempt + 1}/{_STAGE_RETRIES}: {e}",
                )
                continue
            await ctx.deps.add_event("agent_limit", "Analyst", f"Limit reached: {str(e)}")
            return LimitedAnalystFindings(warning=f"Analyst hit a limit: {str(e)}")
        except UsageLimitExceeded as e:
            await ctx.deps.add_event("agent_limit", "Analyst", f"Limit reached: {str(e)}")
            return LimitedAnalystFindings(warning=f"Analyst hit a limit: {str(e)}")
        except Exception as e:
            await ctx.deps.add_event("agent_limit", "Analyst", f"Limit reached: {str(e)}")
            return LimitedAnalystFindings(warning=f"Analyst hit a limit: {str(e)}")

    # Defensive fallback — should not be reachable.
    return LimitedAnalystFindings(warning=f"Analyst hit a limit: {last_unexpected}")


@lead_agent.tool
async def run_reporter(
    ctx: RunContext[ResearchContext],
    synthesis_prompt: str,
) -> MarketReport:
    """Delegate to the Reporter agent. Pass a detailed prompt that includes findings so it can synthesize the final report."""
    await ctx.deps.add_event("agent_start", "Reporter", "Starting report synthesis")

    try:
        result = await asyncio.wait_for(
            reporter_agent.run(
                synthesis_prompt,
                deps=ctx.deps,
                usage=ctx.usage,
                usage_limits=UsageLimits(request_limit=8, tool_calls_limit=0),
            ),
            timeout=_AGENT_TIMEOUT,
        )
        await ctx.deps.add_event("agent_end", "Reporter", "Completed report synthesis")
        return result.output

    except asyncio.TimeoutError:
        await ctx.deps.add_event("agent_limit", "Reporter", f"Timeout after {_AGENT_TIMEOUT}s")
        return MarketReport(
            title="Report Generation Timed Out",
            executive_summary=(
                f"The reporter agent timed out after {_AGENT_TIMEOUT}s. "
                "Research and analyst findings were captured and are available for retry."
            ),
            sections=[],
            sources=[],
            markdown_content=(
                f"# Report Timed Out\n\nThe reporter agent did not complete within "
                f"{_AGENT_TIMEOUT}s. Research and analyst findings are stored in the session "
                "and can be accessed via the retry endpoint."
            ),
        )
    except (UsageLimitExceeded, UnexpectedModelBehavior, Exception) as e:
        await ctx.deps.add_event("agent_limit", "Reporter", f"Reporter failed: {str(e)}")
        return MarketReport(
            title="Report Generation Failed",
            executive_summary=(
                f"The reporter agent encountered an error: {str(e)}. "
                "Research and analyst findings were captured and are available for retry."
            ),
            sections=[],
            sources=[],
            markdown_content=(
                f"# Report Failed\n\nError: {str(e)}\n\nResearch and analyst findings are "
                "stored in the session and can be accessed via the retry endpoint."
            ),
        )

