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
        "You are a Reporter synthesizing pharma market research findings into a "
        "publication-ready report. You have NO tools — do NOT attempt any tool calls.\n\n"
        "You will receive a synthesis prompt containing findings from Market Access and "
        "Data Analyst agents. Your job is to:\n"
        "1. Write an informative executive_summary (2-3 paragraphs) that covers key findings.\n"
        "2. Organize findings into clear sections — at minimum: Regulatory Landscape, "
        "Clinical Pipeline, Market Size & Forecast, Competitive Landscape, and "
        "Conclusions & Outlook.\n"
        "3. Cite sources where available; include all URLs in the sources list.\n"
        "4. Populate the markdown_content field with the FULL report as a single "
        "well-formatted Markdown string (include title, all sections, sources).\n\n"
        "Write precisely and concisely for a pharma/biotech audience. Use specific data "
        "and numbers rather than vague language. If data is unavailable for a field, "
        "note the gap rather than fabricating information."
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
