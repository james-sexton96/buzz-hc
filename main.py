"""Entry point for the Multi-Agent Pharma Market Research Tool."""

import argparse
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
    CheckpointSession,
    ResearchSession,
    UsageStats,
    generate_session_id,
    load_checkpoint,
    save_checkpoint,
    save_session,
)


def _default_query() -> str:
    return (
        "Research the market access and competitive landscape for PD-1/PD-L1 inhibitors "
        "in non-small cell lung cancer (NSCLC) in the US and EU."
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pharma Market Research CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python main.py \"NSCLC market access\"\n"
            "  python main.py --resume 20260330_142233_a1b2\n"
            "  python main.py --resume ./reports/checkpoints/20260330_142233_a1b2.checkpoint.json"
        ),
    )
    parser.add_argument(
        "--resume",
        metavar="SESSION_ID_OR_PATH",
        help="Resume a failed run from a checkpoint (session ID or .checkpoint.json path)",
    )
    parser.add_argument(
        "query",
        nargs="*",
        help="Research query (wrap in quotes for multi-word queries)",
    )
    args = parser.parse_args()
    args.query = " ".join(args.query) if args.query else None
    return args


def _print_report(report) -> None:
    """Print a MarketReport to stdout."""
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


def _save_failure_checkpoint(
    session_id: str,
    query: str,
    deps: ResearchContext,
    exc: BaseException,
) -> None:
    """Inspect deps for partial findings and write a checkpoint file."""
    research = getattr(deps, "research_findings", None)
    analyst = getattr(deps, "analyst_findings", None)

    if analyst is not None:
        stage = "analyst"
    elif research is not None:
        stage = "research"
    else:
        stage = "none"

    checkpoint = CheckpointSession(
        session_id=session_id,
        query=query,
        research_findings=research,
        analyst_findings=analyst,
        events=deps.events,
        stage_reached=stage,
        failure_reason=str(exc),
    )
    saved = save_checkpoint(checkpoint)

    label = "Interrupted" if isinstance(exc, KeyboardInterrupt) else f"Failed: {exc}"
    print(f"\n{label}", file=sys.stderr)
    print(f"Checkpoint saved → {saved}", file=sys.stderr)
    print(f"Resume with:  python main.py --resume {session_id}", file=sys.stderr)


async def _handle_resume(session_id_or_path: str) -> None:
    """Load a checkpoint and run remaining pipeline stages."""
    from app.cli_resume import resume_from_checkpoint

    try:
        checkpoint = load_checkpoint(session_id_or_path)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(
        f"Resuming session {checkpoint.session_id} (stage reached: {checkpoint.stage_reached})",
        file=sys.stderr,
    )
    if checkpoint.failure_reason:
        print(f"  Previous failure: {checkpoint.failure_reason}", file=sys.stderr)
    print(f"Query: {checkpoint.query}\n")

    try:
        session = await resume_from_checkpoint(checkpoint)
    except (Exception, KeyboardInterrupt) as exc:
        print(f"\nResume failed: {exc}", file=sys.stderr)
        print(
            f"Original checkpoint preserved at: "
            f"./reports/checkpoints/{checkpoint.session_id}.checkpoint.json",
            file=sys.stderr,
        )
        sys.exit(1)

    _print_report(session.report)

    usage_data_str = (
        f"requests={session.usage.requests}, tokens={session.usage.total_tokens}"
    )
    print(f"\n---\nUsage: {usage_data_str}", file=sys.stderr)

    saved_json = save_session(session)
    print(f"Session saved → {saved_json}", file=sys.stderr)

    # Remove checkpoint now that the run completed successfully
    ckpt_path = Path(f"./reports/checkpoints/{checkpoint.session_id}.checkpoint.json")
    if ckpt_path.exists():
        ckpt_path.unlink()

    # Optionally export PDF
    try:
        from app.export_pdf import save_pdf
        pdf_path = save_pdf(session.report, Path(f"./reports/{session.session_id}.pdf"))
        print(f"PDF report saved → {pdf_path}", file=sys.stderr)
    except Exception as e:
        print(f"PDF export skipped: {e}", file=sys.stderr)


async def main() -> None:
    args = _parse_args()

    if args.resume:
        await _handle_resume(args.resume)
        return

    query = args.query or _default_query()
    session_id = generate_session_id()

    # Print session ID before anything runs so the user can always resume
    print(f"Session ID: {session_id}", file=sys.stderr)
    print(f"  (if interrupted, resume with: python main.py --resume {session_id})", file=sys.stderr)
    print("Running research for:", query, "\n")

    deps = ResearchContext(
        tavily_api_key=os.environ.get("TAVILY_API_KEY", ""),
        db_connection=None,
        session_state=None,
    )

    try:
        result = await lead_agent.run(
            query,
            deps=deps,
            usage_limits=UsageLimits(request_limit=20, tool_calls_limit=15),
        )
    except (Exception, KeyboardInterrupt) as exc:
        _save_failure_checkpoint(session_id, query, deps, exc)
        sys.exit(1)

    report = result.output
    _print_report(report)

    usage_data = result.usage()
    if usage_data:
        print("\n---\nUsage:", usage_data, file=sys.stderr)

    session = ResearchSession(
        session_id=session_id,
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
        pdf_path = save_pdf(report, Path(f"./reports/{session_id}.pdf"))
        print(f"PDF report saved → {pdf_path}", file=sys.stderr)
    except Exception as e:
        print(f"PDF export skipped: {e}", file=sys.stderr)


if __name__ == "__main__":
    asyncio.run(main())
