"""Reporter Agent: synthesize findings into a publication-ready Markdown report.

Part 4: Adds a parallel streaming-only agent (`_reporter_stream_agent`) with
`output_type=str` and a `stream_reporter_text` helper. The streaming agent
emits free-form Markdown text via `stream_text(delta=True)` so the Run-screen
"Emerging draft" panel can show word-by-word output. The structured
`reporter_agent` (`output_type=MarketReport`) still runs after streaming —
it is the authoritative producer of the typed `MarketReport`, gated by
`output_validator`. Pydantic-ai's `stream_text()` is incompatible with
structured outputs (hard-coded UserError), so the two-call hybrid is required.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic_ai import Agent, ModelRetry, RunContext

from app.context import ResearchContext
from app.llm import get_model, get_retries
from app.schema import AnalystFindings, MarketAccessFindings, MarketReport

if TYPE_CHECKING:
    from api.stream import StreamingResearchContext

model = get_model()

reporter_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=MarketReport,
    retries=get_retries(),
    instructions=(
        "You are a Healthcare Commercial Intelligence Reporter. Your audience is "
        "pharmaceutical commercial teams, market access leads, and payer strategy "
        "professionals. Write like a senior analyst at a healthcare consulting firm — "
        "precise, commercially actionable, and evidence-grounded. You have NO tools — "
        "do NOT attempt any tool calls.\n\n"
        "You will receive a synthesis prompt that includes a QUESTION ARCHETYPE. Use it "
        "to select the appropriate section structure from the menus below.\n\n"
        "SECTION STRUCTURE BY ARCHETYPE:\n\n"
        "coverage/formulary:\n"
        "  1. Executive Summary\n"
        "  2. Payer Coverage Landscape\n"
        "  3. Formulary Tier & Positioning\n"
        "  4. Prior Authorization & Step Therapy Requirements\n"
        "  5. Access Barriers & Utilization Management\n"
        "  6. Competitive Payer Positioning\n"
        "  7. Gaps & Data Confidence\n"
        "  8. Key Takeaways & Implications\n\n"
        "volume/prescribing:\n"
        "  1. Executive Summary\n"
        "  2. Prescription Volume Overview (TRx/NBRx Trends)\n"
        "  3. Patient Share & Market Share Analysis\n"
        "  4. Channel Mix (Retail vs Specialty Pharmacy)\n"
        "  5. Analogue Launch Benchmarks\n"
        "  6. Competitive Rx Landscape\n"
        "  7. Payer Access Context\n"
        "  8. Gaps & Data Confidence\n"
        "  9. Key Takeaways & Implications\n\n"
        "care-delivery:\n"
        "  1. Executive Summary\n"
        "  2. Administration Route & Care Setting\n"
        "  3. Specialty Pharmacy & REMS Requirements\n"
        "  4. Site-of-Care Economics\n"
        "  5. Payer Site-of-Care Restrictions\n"
        "  6. Channel Mix & Dispensing Data\n"
        "  7. Competitive Site-of-Care Landscape\n"
        "  8. Gaps & Data Confidence\n"
        "  9. Key Takeaways & Implications\n\n"
        "regulatory/pipeline:\n"
        "  1. Executive Summary\n"
        "  2. Regulatory Status (FDA/EMA/other)\n"
        "  3. Clinical Pipeline\n"
        "  4. HEOR & Real-World Evidence\n"
        "  5. Market Access & Payer Readiness\n"
        "  6. Competitive Regulatory Landscape\n"
        "  7. Gaps & Data Confidence\n"
        "  8. Key Takeaways & Implications\n\n"
        "market-sizing/competitive:\n"
        "  1. Executive Summary\n"
        "  2. Market Size & Growth Forecast\n"
        "  3. Competitive Landscape & Market Share\n"
        "  4. Prescription Volume Benchmarks (TRx/NBRx)\n"
        "  5. Analogue Launch Comparisons\n"
        "  6. Payer & Access Dynamics\n"
        "  7. Regulatory & Pipeline Context\n"
        "  8. Gaps & Data Confidence\n"
        "  9. Key Takeaways & Implications\n\n"
        "multi-dimensional:\n"
        "  Use Executive Summary + a hybrid of the two most relevant archetype structures "
        "above, then Gaps & Data Confidence, then Key Takeaways & Implications.\n\n"
        "MANDATORY SECTIONS (every report, every archetype):\n"
        "- 'Gaps & Data Confidence': scan every field in both findings objects. Any field "
        "that is null, an empty list, or contains 'data not available' MUST be listed "
        "explicitly here — what was searched for, what was not found, and any known "
        "staleness or date limitations.\n"
        "- 'Key Takeaways & Implications': 3-5 bulleted commercial insights.\n\n"
        "EXECUTIVE SUMMARY STRUCTURE (3 paragraphs):\n"
        "  Paragraph 1: Headline answer to the research question in 1-2 sentences.\n"
        "  Paragraph 2: Most commercially important findings across access, volume, and "
        "competitive dimensions.\n"
        "  Paragraph 3: The primary risk, gap, or caveat a decision-maker must know.\n\n"
        "OUTPUT REQUIREMENTS:\n"
        "1. Populate sections with the archetype-appropriate structure above.\n"
        "2. Every section must draw only from the provided findings — no external facts.\n"
        "3. Cite sources; include all URLs from the findings in the sources list.\n"
        "4. Populate markdown_content with the FULL report as a single well-formatted "
        "Markdown string (title, all sections, sources appendix).\n"
        "5. country_mix (OPTIONAL): if and ONLY if the findings contain country-level "
        "share or spend data (e.g. EU5, US, regional breakdowns), populate country_mix "
        "with one CountryMixEntry per country. Otherwise leave country_mix as null.\n"
        "6. scenario_probabilities (OPTIONAL): if and ONLY if the findings contain "
        "scenario-style assessments (base/bull/bear, optimistic/pessimistic, etc.), "
        "populate scenario_probabilities with one ScenarioEntry per scenario. "
        "Otherwise leave scenario_probabilities as null.\n\n"
        "ANTI-HALLUCINATION: If a field in the agent findings is null, empty, or 'data "
        "not available', write 'Data not available' in the relevant report section and "
        "log it in Gaps & Data Confidence. Never present estimated values as confirmed "
        "data. Never fabricate payer policies, trial results, or market share figures. "
        "For country_mix and scenario_probabilities specifically: populate ONLY from "
        "data present in the provided findings; if absent, leave as null. Do NOT invent "
        "country shares, spend figures, or scenario probabilities."
    ),
)


@reporter_agent.output_validator
async def validate_reporter_output(
    ctx: RunContext[ResearchContext], output: MarketReport
) -> MarketReport:
    """Reject skeleton reports — require title, summary, sections, and markdown content."""
    if not output.title or not output.executive_summary:
        raise ModelRetry(
            "Your report is missing essentials. Both 'title' and 'executive_summary' "
            "must contain meaningful text. Synthesize the research findings."
        )
    if not output.sections:
        raise ModelRetry(
            "Your report has no sections. Include at minimum the sections required for "
            "the question archetype, plus the mandatory 'Gaps & Data Confidence' and "
            "'Key Takeaways & Implications' sections."
        )
    if not output.markdown_content:
        raise ModelRetry(
            "markdown_content must be populated with the full formatted report as a "
            "single Markdown string including all sections and a sources appendix."
        )
    return output


# ---------------------------------------------------------------------------
# Part 4: streaming-only text agent + helper
#
# `stream_text()` is incompatible with `output_type=MarketReport`
# (UserError raised in pydantic-ai source). This separate agent emits
# free-form Markdown text token-by-token via `stream_text(delta=True)`
# purely for UX — the structured `reporter_agent` above remains the
# authoritative producer of the typed `MarketReport`.
# ---------------------------------------------------------------------------

_reporter_stream_agent = Agent(
    model,
    deps_type=ResearchContext,
    output_type=str,
    retries=get_retries(),
    instructions=(
        "You are a Healthcare Commercial Intelligence Reporter writing a draft for "
        "live streaming display. Synthesize the provided market access and analyst "
        "findings into a well-structured Markdown report.\n\n"
        "Begin with the title (as a # H1 heading), then the executive summary "
        "(3 paragraphs: headline answer; key commercial findings; primary risk/caveat), "
        "then the body sections appropriate to the question archetype, then a "
        "'Gaps & Data Confidence' section, then 'Key Takeaways & Implications'.\n\n"
        "Write only narrative prose and headings. Do NOT call any tools. Do NOT emit "
        "JSON. Every claim must be supported by the provided findings — no external "
        "facts. Where findings are null, empty, or 'data not available', write "
        "'Data not available' rather than guessing.\n\n"
        "Cite sources inline using [N] markers where N is the 1-based index into the "
        "sources URL list. The full report is your output as plain Markdown text."
    ),
)


async def stream_reporter_text(
    synthesis_prompt: str,
    ctx: "StreamingResearchContext",
) -> str:
    """Stream the reporter's narrative text into the SSE token queue.

    For each delta chunk emitted by pydantic-ai's `stream_text(delta=True)`,
    call `ctx.put_token(chunk)` to enqueue it for the SSE writer. Always
    calls `ctx.close_token_stream()` in `finally` so the token-stream
    sentinel is set even if the streaming agent raises mid-run.

    Returns the accumulated text (concatenation of all chunks) — currently
    unused by the route but kept for symmetry with the structured call.

    Caller is responsible for the four-branch exception discrimination
    (TimeoutError / UnexpectedModelBehavior / UsageLimitExceeded / Exception).
    This helper only handles the queue lifecycle.
    """
    accumulated: list[str] = []
    try:
        async with _reporter_stream_agent.run_stream(
            synthesis_prompt,
            deps=ctx,
        ) as stream_result:
            async for chunk in stream_result.stream_text(delta=True, debounce_by=0.01):
                if chunk:
                    accumulated.append(chunk)
                    ctx.put_token(chunk)
    finally:
        ctx.close_token_stream()
    return "".join(accumulated)
