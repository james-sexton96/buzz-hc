"""Entry point for the Multi-Agent Pharma Market Research Tool."""

import asyncio
import os
import sys

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
    if result.usage():
        print("\n---\nUsage:", result.usage(), file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
