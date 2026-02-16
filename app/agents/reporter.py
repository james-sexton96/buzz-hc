"""Reporter Agent: synthesize findings into a publication-ready Markdown report."""

from pydantic_ai import Agent, ModelRetry, RunContext

from app.context import ResearchContext
from app.llm import get_model, get_retries
from app.schema import AnalystFindings, MarketAccessFindings, MarketReport

model = get_model()

reporter_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=MarketReport,
    retries=get_retries(),
    instructions=(
        "You are a Reporter. You receive structured findings from Market Access and Data Analyst agents. "
        "Synthesize them into a single publication-ready Markdown report. "
        "Output a MarketReport with: title, executive_summary, sections (heading + content for each section), "
        "sources (list of URLs or references), and optionally markdown_content (full report as one string). "
        "Write clearly for a pharma/biotech audience."
    ),
)


@reporter_agent.output_validator
async def validate_reporter_output(
    ctx: RunContext[ResearchContext], output: MarketReport
) -> MarketReport:
    """Only reject if the report is a skeleton — title and summary must exist."""
    if not output.title or not output.executive_summary:
        raise ModelRetry(
            "Your report is missing essentials. Both 'title' and 'executive_summary' "
            "must contain meaningful text. Synthesize the research findings."
        )
    return output
