"""Reporter Agent: synthesize findings into a publication-ready Markdown report."""

from pydantic_ai import Agent, RunContext

from app.context import ResearchContext
from app.llm import get_model
from app.schema import AnalystFindings, MarketAccessFindings, MarketReport

model = get_model()

reporter_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=MarketReport,
    instructions=(
        "You are a Reporter. You receive structured findings from Market Access and Data Analyst agents. "
        "Synthesize them into a single publication-ready Markdown report. "
        "Output a MarketReport with: title, executive_summary, sections (heading + content for each section), "
        "sources (list of URLs or references), and optionally markdown_content (full report as one string). "
        "Write clearly for a pharma/biotech audience."
    ),
)
