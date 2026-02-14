import asyncio
import os
import sys
import streamlit as st
from datetime import datetime

# Ensure project root is on path
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from pydantic_ai import UsageLimits

from app.agents.lead import lead_agent
from app.context import ResearchContext
from app.scenarios import SCENARIOS

# Page configuration
st.set_page_config(
    page_title="Buzz Healthcare | Research Swarm",
    page_icon="🐝",
    layout="wide",
)

st.title("🐝 Buzz Healthcare (Buzz-HC)")
st.markdown("Monitor the swarm of agents performing pharma market research in real-time.")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    tavily_api_key = st.text_input("Tavily API Key", value=os.environ.get("TAVILY_API_KEY", ""), type="password")
    
    st.header("Scenarios")
    selected_scenario = st.selectbox(
        "Select a benchmark scenario",
        options=range(len(SCENARIOS)),
        format_func=lambda i: SCENARIOS[i]["label"]
    )
    
    scenario = SCENARIOS[selected_scenario]
    st.info(scenario["description"])

# Main query input
query = st.text_area("Research Query", value=scenario["query"] if scenario["query"] else "", height=100)

if st.button("🚀 Run Research", type="primary"):
    if not query.strip():
        st.error("Please enter a research query.")
    elif not tavily_api_key.strip():
        st.error("Tavily API Key is required.")
    else:
        # State management
        deps = ResearchContext(
            tavily_api_key=tavily_api_key,
            db_connection=None,
            session_state={},
        )
        
        # UI Elements for progress
        progress_container = st.container()
        
        with progress_container:
            with st.status("Agent workflow in progress...", expanded=True) as status:
                log_container = st.empty()
                
                async def run_research():
                    try:
                        # Add initial event
                        deps.add_event("info", "System", "Starting research pipeline...")
                        
                        # Background task to refresh logs
                        async def update_logs():
                            last_count = 0
                            while True:
                                if len(deps.events) > last_count:
                                    with log_container.container():
                                        for event in deps.events:
                                            icon = "🤖" if "agent" in event.event_type else "🛠️" if "tool" in event.event_type else "ℹ️"
                                            st.markdown(f"{icon} **{event.source}** ({event.event_type}): {event.message}")
                                    last_count = len(deps.events)
                                await asyncio.sleep(0.5)

                        log_task = asyncio.create_task(update_logs())
                        
                        # Run the lead agent
                        result = await lead_agent.run(
                            query,
                            deps=deps,
                            usage_limits=UsageLimits(request_limit=30, tool_calls_limit=20),
                        )
                        
                        log_task.cancel()
                        status.update(label="Research Complete!", state="complete", expanded=False)
                        return result
                    except Exception as e:
                        status.update(label="Error occurred", state="error")
                        st.error(f"Error: {e}")
                        return None

                # Execute
                try:
                    # In Streamlit, we might already have an event loop in some environments
                    # but typically not on the script execution thread.
                    # This is a safe way to run the async task.
                    result = asyncio.run(run_research())
                except RuntimeError:
                    # Fallback for environments with an existing loop
                    loop = asyncio.get_event_loop()
                    result = loop.run_until_complete(run_research())

        if result:
            st.success("✅ Research task complete!")
            
            # Use tabs for a cleaner report view
            report_tab, trace_tab = st.tabs(["📄 Final Report", "🔍 Research Trace"])
            
            with report_tab:
                report = result.output
                # Display report
                if hasattr(report, "markdown_content") and report.markdown_content:
                    st.markdown(report.markdown_content)
                else:
                    st.header(report.title)
                    st.markdown(f"**Executive Summary:** {report.executive_summary}")
                    
                    for section in getattr(report, "sections", []):
                        with st.expander(section.heading, expanded=True):
                            st.markdown(section.content)
                    
                    if getattr(report, "sources", None):
                        st.subheader("Sources")
                        for s in report.sources:
                            st.markdown(f"- {s}")
            
            with trace_tab:
                for event in deps.events:
                    icon = "🤖" if "agent" in event.event_type else "🛠️" if "tool" in event.event_type else "ℹ️"
                    st.markdown(f"{icon} **{event.source}** ({event.event_type}): {event.message}")
                    if event.details:
                        with st.expander("Details"):
                            st.write(event.details)
            
            with st.sidebar:
                st.divider()
                st.header("📊 Usage Stats")
                usage = result.usage()
                st.write(f"- Requests: {usage.requests}")
                st.write(f"- Tokens: {usage.total_tokens}")
