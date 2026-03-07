import asyncio
import os
import sys
import streamlit as st
from datetime import datetime
from pathlib import Path

# Ensure project root is on path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

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
    list_sessions,
    load_session,
    save_session,
)
from app.schema import MarketReport, WorkflowEvent
from app.scenarios import SCENARIOS

# ---------------------------------------------------------------------------
# PDF export — optional; degrade gracefully if weasyprint isn't installed
# ---------------------------------------------------------------------------
try:
    from app.export_pdf import export_pdf as _export_pdf
    PDF_AVAILABLE = True
except Exception:
    PDF_AVAILABLE = False


# ---------------------------------------------------------------------------
# Shared rendering helpers
# ---------------------------------------------------------------------------

def _render_report(report: MarketReport, session_id: str = "") -> None:
    """Render a MarketReport in Streamlit, with an optional PDF download."""
    if report.markdown_content:
        st.markdown(report.markdown_content)
    else:
        st.header(report.title)
        st.markdown(f"**Executive Summary:** {report.executive_summary}")

        for section in getattr(report, "sections", []) or []:
            with st.expander(section.heading, expanded=True):
                st.markdown(section.content)

        if getattr(report, "sources", None):
            st.subheader("Sources")
            for s in report.sources:
                st.markdown(f"- {s}")

    # PDF download button
    if PDF_AVAILABLE:
        try:
            pdf_bytes = _export_pdf(report)
            filename = f"buzz_hc_report_{session_id or 'export'}.pdf"
            st.download_button(
                label="⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
            )
        except Exception as e:
            st.warning(f"PDF export unavailable: {e}")
    else:
        st.caption(
            "PDF export requires weasyprint. "
            "Install with: `uv add weasyprint markdown`"
        )


def _render_trace(events: list[WorkflowEvent]) -> None:
    """Render workflow trace events in Streamlit."""
    for event in events:
        icon = (
            "🤖" if "agent" in event.event_type
            else "🛠️" if "tool" in event.event_type
            else "ℹ️"
        )
        st.markdown(
            f"{icon} **{event.source}** ({event.event_type}): {event.message}"
        )
        if event.details:
            with st.expander("Details"):
                st.write(event.details)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Buzz Healthcare | Research Swarm",
    page_icon="🐝",
    layout="wide",
)

st.title("🐝 Buzz Healthcare (Buzz-HC)")
st.markdown(
    "Monitor the swarm of agents performing pharma market research in real-time."
)

# ---------------------------------------------------------------------------
# Sidebar — configuration + past sessions
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Configuration")
    tavily_api_key = st.text_input(
        "Tavily API Key",
        value=os.environ.get("TAVILY_API_KEY", ""),
        type="password",
    )

    st.header("Scenarios")
    selected_scenario = st.selectbox(
        "Select a benchmark scenario",
        options=range(len(SCENARIOS)),
        format_func=lambda i: SCENARIOS[i]["label"],
    )

    scenario = SCENARIOS[selected_scenario]
    st.info(scenario["description"])

    # -----------------------------------------------------------------------
    # Past Sessions browser
    # -----------------------------------------------------------------------
    st.divider()
    st.header("📂 Past Sessions")

    past_sessions = list_sessions()
    if past_sessions:
        session_idx = st.selectbox(
            "Load a previous session",
            options=range(len(past_sessions)),
            format_func=lambda i: (
                f"{past_sessions[i]['timestamp']} — {past_sessions[i]['query']}"
            ),
            key="session_browser",
        )
        if st.button("📂 Load Session", key="load_session_btn"):
            loaded = load_session(Path(past_sessions[session_idx]["filepath"]))
            st.session_state["loaded_session"] = loaded
            st.rerun()
    else:
        st.caption("No saved sessions yet. Run a research query to create one.")

# ---------------------------------------------------------------------------
# Main query area
# ---------------------------------------------------------------------------

query = st.text_area(
    "Research Query",
    value=scenario["query"] if scenario["query"] else "",
    height=100,
)

# ---------------------------------------------------------------------------
# Loaded session view (shown instead of / above new-run results)
# ---------------------------------------------------------------------------

if "loaded_session" in st.session_state:
    loaded: ResearchSession = st.session_state["loaded_session"]
    st.info(
        f"📂 Viewing saved session from **{loaded.timestamp.strftime('%Y-%m-%d %H:%M')}**  "
        f"— *{loaded.query[:100]}*"
    )
    report_tab, trace_tab = st.tabs(["📄 Final Report", "🔍 Research Trace"])

    with report_tab:
        if loaded.report:
            _render_report(loaded.report, session_id=loaded.session_id)
        else:
            st.warning("No report saved for this session.")

    with trace_tab:
        if loaded.events:
            _render_trace(loaded.events)
        else:
            st.caption("No trace events saved for this session.")

    if st.button("✖ Clear loaded session"):
        del st.session_state["loaded_session"]
        st.rerun()

    st.divider()

# ---------------------------------------------------------------------------
# Run Research button
# ---------------------------------------------------------------------------

if st.button("🚀 Run Research", type="primary"):
    if not query.strip():
        st.error("Please enter a research query.")
    elif not tavily_api_key.strip():
        st.error("Tavily API Key is required.")
    else:
        deps = ResearchContext(
            tavily_api_key=tavily_api_key,
            db_connection=None,
            session_state={},
        )

        progress_container = st.container()

        with progress_container:
            with st.status("Agent workflow in progress...", expanded=True) as status:
                log_container = st.empty()

                async def run_research():
                    try:
                        deps.add_event("info", "System", "Starting research pipeline...")

                        async def update_logs():
                            last_count = 0
                            while True:
                                if len(deps.events) > last_count:
                                    with log_container.container():
                                        for event in deps.events:
                                            icon = (
                                                "🤖" if "agent" in event.event_type
                                                else "🛠️" if "tool" in event.event_type
                                                else "ℹ️"
                                            )
                                            st.markdown(
                                                f"{icon} **{event.source}** "
                                                f"({event.event_type}): {event.message}"
                                            )
                                    last_count = len(deps.events)
                                await asyncio.sleep(0.5)

                        log_task = asyncio.create_task(update_logs())

                        result = await lead_agent.run(
                            query,
                            deps=deps,
                            usage_limits=UsageLimits(request_limit=50),
                        )

                        log_task.cancel()
                        status.update(
                            label="Research Complete!", state="complete", expanded=False
                        )
                        return result
                    except Exception as e:
                        status.update(label="Error occurred", state="error")
                        st.error(f"Error: {e}")
                        return None

                # Execute
                try:
                    result = asyncio.run(run_research())
                except RuntimeError:
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(run_research())

        if result:
            # Auto-save session
            usage_data = result.usage()
            session = ResearchSession(
                session_id=generate_session_id(),
                query=query,
                report=result.output,
                events=deps.events,
                usage=UsageStats(
                    requests=usage_data.requests if usage_data else 0,
                    total_tokens=usage_data.total_tokens if usage_data else 0,
                    request_tokens=getattr(usage_data, "request_tokens", 0) or 0,
                    response_tokens=getattr(usage_data, "response_tokens", 0) or 0,
                ),
            )
            saved_path = save_session(session)
            st.toast(f"✅ Session saved → {saved_path}")

            st.success("✅ Research task complete!")

            report_tab, trace_tab = st.tabs(["📄 Final Report", "🔍 Research Trace"])

            with report_tab:
                _render_report(result.output, session_id=session.session_id)

            with trace_tab:
                _render_trace(deps.events)

            with st.sidebar:
                st.divider()
                st.header("📊 Usage Stats")
                if usage_data:
                    st.write(f"- Requests: {usage_data.requests}")
                    st.write(f"- Tokens: {usage_data.total_tokens}")
