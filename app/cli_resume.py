"""CLI resume: run remaining pipeline stages from a checkpoint file."""

import os
import sys

from pydantic_ai import UsageLimits

from app.context import ResearchContext
from app.history import CheckpointSession, ResearchSession, UsageStats

_SYNTHESIS_PROMPT = (
    "RESEARCH QUESTION: {query}\n\n"
    "QUESTION ARCHETYPE: {question_archetype}\n"
    "(Use this to select the appropriate report section structure per your instructions.)\n\n"
    "PRIMARY RESEARCH DIMENSIONS: {primary_dimensions}\n\n"
    "MARKET ACCESS FINDINGS (from Researcher Agent):\n{research}\n\n"
    "ANALYST FINDINGS (from Analyst Agent):\n{analyst}\n\n"
    "REPORTER INSTRUCTIONS:\n"
    "1. Use QUESTION ARCHETYPE to select the appropriate section structure.\n"
    "2. Every section must draw only from the findings above — no external facts.\n"
    "3. For any null, empty, or 'data not available' field, note the gap explicitly in "
    "the Gaps & Data Confidence section.\n"
    "4. The 'Gaps & Data Confidence' section is MANDATORY in every report.\n"
    "5. Populate sources with every URL present in the findings.\n"
    "6. Executive summary: paragraph 1 = headline answer, paragraph 2 = key commercial "
    "findings, paragraph 3 = primary caveat or risk.\n"
    "7. Populate markdown_content with the complete formatted report as a single Markdown string."
)


async def resume_from_checkpoint(checkpoint: CheckpointSession) -> ResearchSession:
    """Resume a failed pipeline run, skipping stages already in the checkpoint.

    Calls researcher_agent, analyst_agent, and reporter_agent directly
    (bypassing lead_agent) so completed stages can be skipped cleanly.
    Mirrors the pattern in api/routes/run.py:_run_reporter_only().
    """
    # Import inside function so get_model() reads env vars after .env is loaded
    from app.agents.analyst import analyst_agent
    from app.agents.reporter import reporter_agent
    from app.agents.researcher import researcher_agent

    deps = ResearchContext(
        tavily_api_key=os.environ.get("TAVILY_API_KEY", ""),
        db_connection=None,
        session_state=None,
        events=list(checkpoint.events),  # carry forward prior event trace
    )
    query = checkpoint.query
    research = checkpoint.research_findings
    analyst = checkpoint.analyst_findings

    # --- Stage 1: Research ---
    if research is None:
        print("[resume] Running researcher agent...", file=sys.stderr)
        deps.add_event("info", "CLI", "Resuming: running researcher agent")
        result = await researcher_agent.run(
            f"Research market access for: {query}",
            deps=deps,
            usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8),
        )
        research = result.output
    else:
        print("[resume] Researcher: loaded from checkpoint.", file=sys.stderr)
        deps.add_event("info", "CLI", "Resuming: researcher findings loaded from checkpoint")
    deps.research_findings = research

    # --- Stage 2: Analyst ---
    if analyst is None:
        print("[resume] Running analyst agent...", file=sys.stderr)
        deps.add_event("info", "CLI", "Resuming: running analyst agent")
        result = await analyst_agent.run(
            f"Analyze market for: {query}",
            deps=deps,
            usage_limits=UsageLimits(request_limit=10, tool_calls_limit=8),
        )
        analyst = result.output
    else:
        print("[resume] Analyst: loaded from checkpoint.", file=sys.stderr)
        deps.add_event("info", "CLI", "Resuming: analyst findings loaded from checkpoint")
    deps.analyst_findings = analyst

    # --- Stage 3: Reporter (always runs) ---
    print("[resume] Running reporter agent...", file=sys.stderr)
    deps.add_event("info", "CLI", "Resuming: running reporter agent")
    synthesis_prompt = _SYNTHESIS_PROMPT.format(
        query=query,
        question_archetype="multi-dimensional",
        primary_dimensions="market access, payer coverage, market sizing, competitive landscape",
        research=research.model_dump_json(indent=2) if research else "Not available",
        analyst=analyst.model_dump_json(indent=2) if analyst else "Not available",
    )
    result = await reporter_agent.run(
        synthesis_prompt,
        deps=deps,
        usage_limits=UsageLimits(request_limit=8, tool_calls_limit=0),
    )
    usage_data = result.usage()

    return ResearchSession(
        session_id=checkpoint.session_id,  # preserve same ID for continuity
        query=query,
        report=result.output,
        events=deps.events,
        usage=UsageStats(
            requests=getattr(usage_data, "requests", 0) or 0,
            total_tokens=getattr(usage_data, "total_tokens", 0) or 0,
            request_tokens=getattr(usage_data, "request_tokens", 0) or 0,
            response_tokens=getattr(usage_data, "response_tokens", 0) or 0,
        ),
    )
