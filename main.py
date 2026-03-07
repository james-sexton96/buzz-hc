"""Entry point for the Multi-Agent Pharma Market Research Tool."""

import asyncio
import os
import sys
from pathlib import Path

# Ensure project root is on path when running as script
if __name__ == "__main__" and os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from app.startup import check_dependencies
check_dependencies()

from pydantic_ai import UsageLimits

from app.agents.lead import lead_agent
from app.context import ResearchContext
from app.history import (
    ResearchSession,
    UsageStats,
    generate_session_id,
    save_session,
)


def _default_query() -> str:
    return (
        "Research the market access and competitive landscape for PD-1/PD-L1 inhibitors "
        "in non-small cell lung cancer (NSCLC) in the US and EU."
    )


async def main() -> None:
    tavily_api_key = os.environ.get("TAVILY_API_KEY", "")
    deps = ResearchContext(
        tavily_api_key=tavily_api_key,
        db_connection=None,
        session_state=None,
    )
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else _default_query()
    print("Running research for:", query, "\n")

    result = await lead_agent.run(
        query,
        deps=deps,
        usage_limits=UsageLimits(request_limit=20, tool_calls_limit=15),
    )
    report = result.output

    # Print report to stdout
    if hasattr(report, "markdown_content") and report.markdown_content:
        print(report.markdown_content)
    elif hasattr(report, "title"):
        print(f"# {report.title}\n")
        print(report.executive_summary)
        for section in getattr(report, "sections", []) or []:
            print(f"\n## {section.heading}\n")
            print(section.content)
        if getattr(report, "sources", None):
            print("\n## Sources\n")
            for s in report.sources:
                print(f"- {s}")
    else:
        print(report)

    usage_data = result.usage()
    if usage_data:
        print("\n---\nUsage:", usage_data, file=sys.stderr)

    # Auto-save session to ./reports/
    session = ResearchSession(
        session_id=generate_session_id(),
        query=query,
        report=report,
        events=deps.events,
        usage=UsageStats(
            requests=usage_data.requests if usage_data else 0,
            total_tokens=usage_data.total_tokens if usage_data else 0,
            request_tokens=getattr(usage_data, "request_tokens", 0) or 0,
            response_tokens=getattr(usage_data, "response_tokens", 0) or 0,
        ),
    )
    saved_json = save_session(session)
    print(f"\nSession saved → {saved_json}", file=sys.stderr)

    # Optionally export PDF (requires weasyprint)
    try:
        from app.export_pdf import save_pdf
        pdf_path = save_pdf(report, Path(f"./reports/{session.session_id}.pdf"))
        print(f"PDF report saved → {pdf_path}", file=sys.stderr)
    except Exception as e:
        print(f"PDF export skipped: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
