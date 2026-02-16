# Buzz Healthcare (Buzz-HC)

**Buzz Healthcare (Buzz-HC)** is a specialized multi-agent research tool designed for the healthcare and pharmaceutical markets. The name "Buzz" reflects the "swarm" of intelligent agents that collaborate to perform deep research, analyze complex data, and generate publication-ready market reports.

Built with **PydanticAI**, Buzz-HC utilizes specialized prompting tailored for the pharma industry, ensuring high-quality insights into regulatory landscapes, clinical trials, and market dynamics.

## Key Features

- **Swarm Intelligence**: Multiple specialized agents (Lead, Researcher, Analyst, Reporter) work in parallel to tackle complex research tasks.
- **Healthcare-Specialized Prompting**: Expert-level prompts for regulatory analysis (FDA/EMA), clinical trial synthesis, and pharmaceutical market sizing.
- **Real-Time Monitoring UI**: A Streamlit-based dashboard to track the agent "swarm" as they work, providing a transparent view of the research process.
- **Deep Research Capabilities**: Integrates **Crawl4AI** for adaptive scraping of JS-heavy pharma portals and **Tavily** for broad web intelligence.
- **Structured Outputs**: All research is synthesized into type-safe, structured reports using Pydantic V2 models.

## Architecture: The Swarm

1.  **Lead Researcher (Orchestrator)**: Receives the query, plans the research strategy, and delegates tasks to the swarm.
2.  **Market Access Agent (Researcher)**: Specialized in FDA/EMA regulatory data, clinical trial status (ClinicalTrials.gov), and the payer/reimbursement landscape.
3.  **Data Analyst Agent**: Focused on market sizing, competitive landscape mapping, and financial projections.
4.  **Reporter Agent**: The final synthesizer that compiles all findings into a structured, publication-ready Markdown report for a pharma/biotech audience.

## Setup

1.  **Clone and run the setup script**
    ```bash
    cd buzz-hc
    bash setup-dev.sh
    ```
    This installs Python dependencies, the Playwright Chromium browser (for Crawl4AI deep scraping), and creates a `.env` file from the template.

2.  **Configure your environment**
    Edit `.env` with your LLM provider and API keys:
    - `LLM_PROVIDER=ollama` (default)
    - `LLM_MODEL=ministral-3`
    - `TAVILY_API_KEY=` (Required for search)

    > **Note:** Playwright Chromium is optional. Without it, `deep_scrape` is unavailable but the agents will still work using Tavily search and ClinicalTrials.gov.

## Usage

### Real-Time Monitoring UI (Recommended)
The Streamlit UI provides the best experience, allowing you to watch the agents work in real-time, view research traces, and browse the final report.

```bash
uv run streamlit run app/ui.py
```

### CLI
For quick research tasks directly from the terminal:
```bash
# Default query
uv run python main.py

# Custom query
uv run python main.py "Market access for CAR-T therapies in EU"
```

## Project Layout

```
buzz-hc/
├── main.py                 # CLI Entry point
├── setup-dev.sh            # One-command dev environment setup
├── app/
│   ├── ui.py               # Streamlit Monitoring UI
│   ├── startup.py          # Pre-flight dependency checks
│   ├── agents/             # The Swarm: Lead, Researcher, Analyst, Reporter
│   ├── tools/              # ClinicalTrials.gov, Crawl4AI, Tavily
│   ├── schema.py           # Pydantic V2 models for structured data
│   ├── context.py          # Research context & dependency injection
│   └── scenarios.py        # Predefined research benchmarks
├── pyproject.toml
└── .env.example
```
