# Buzz Healthcare (Buzz-HC)

**Buzz Healthcare (Buzz-HC)** is a specialized multi-agent research tool designed for the healthcare and pharmaceutical markets. The name "Buzz" reflects the "swarm" of intelligent agents that collaborate to perform deep research, analyze complex data, and generate publication-ready market reports.

Built with **PydanticAI**, Buzz-HC utilizes specialized prompting tailored for the pharma industry, ensuring high-quality insights into regulatory landscapes, clinical trials, and market dynamics.

## Key Features

- **Swarm Intelligence**: Multiple specialized agents (Lead, Researcher, Analyst, Reporter) work in parallel to tackle complex research tasks.
- **Healthcare-Specialized Prompting**: Expert-level prompts for regulatory analysis (FDA/EMA), clinical trial synthesis, and pharmaceutical market sizing.
- **Real-Time Monitoring UI**: A Next.js dashboard with live SSE streaming to track the agent swarm as they work.
- **Deep Research Capabilities**: Integrates **Crawl4AI** for adaptive scraping of JS-heavy pharma portals and **Tavily** for broad web intelligence.
- **Structured Outputs**: All research is synthesized into type-safe, structured reports using Pydantic V2 models.
- **Session History**: All research runs are persisted in SQLite and browsable via the UI.

## Architecture

### Agent Swarm

1.  **Lead Researcher (Orchestrator)**: Receives the query, plans the research strategy, and delegates tasks to the swarm.
2.  **Market Access Agent (Researcher)**: Specialized in FDA/EMA regulatory data, clinical trial status (ClinicalTrials.gov), and the payer/reimbursement landscape.
3.  **Data Analyst Agent**: Focused on market sizing, competitive landscape mapping, and financial projections.
4.  **Reporter Agent**: The final synthesizer that compiles all findings into a structured, publication-ready Markdown report for a pharma/biotech audience.

### Stack

```
┌─────────────────────────────────────────┐
│  Next.js 16 (web/)                      │
│  TypeScript · Tailwind CSS              │
│  Real-time SSE streaming, session UI    │
└────────────────┬────────────────────────┘
                 │ HTTP / SSE
┌────────────────▼────────────────────────┐
│  FastAPI (api/)                         │
│  POST /run  · GET /run/{id}/stream      │
│  GET /sessions · GET /sessions/{id}     │
│  POST /run/{id}/retry                   │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  PydanticAI Agent Swarm (app/)          │
│  Lead · Researcher · Analyst · Reporter │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│  SQLite (aiosqlite)                     │
│  Session persistence & checkpoints      │
└─────────────────────────────────────────┘
```

## Setup

1.  **Clone and run the setup script**
    ```bash
    cd buzz-hc
    bash setup-dev.sh
    ```
    This installs Python dependencies, the Playwright Chromium browser (for Crawl4AI deep scraping), and creates a `.env` file from the template.

2.  **Install frontend dependencies**
    ```bash
    cd web && pnpm install
    ```

3.  **Configure your environment**
    Edit `.env` with your LLM provider and API keys:
    - `LLM_PROVIDER=ollama` (default)
    - `LLM_MODEL=qwen3.5:latest`
    - `TAVILY_API_KEY=` (Required for search)

    > **Note:** Playwright Chromium is optional. Without it, `deep_scrape` is unavailable but the agents will still work using Tavily search and ClinicalTrials.gov.

## Usage

### Full Stack (Recommended)

Start the FastAPI backend and Next.js frontend in separate terminals:

```bash
# Terminal 1 — Backend (port 8000)
uv run uvicorn api.main:app --reload

# Terminal 2 — Frontend (port 3000)
cd web && pnpm dev
```

Then open `http://localhost:3000` to submit research queries, watch agent progress via live streaming, browse past sessions, and read the final report.

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
├── main.py                 # CLI entry point
├── setup-dev.sh            # One-command dev environment setup
├── app/                    # PydanticAI agent swarm (do not modify)
│   ├── agents/             # Lead, Researcher, Analyst, Reporter
│   ├── tools/              # ClinicalTrials.gov, Crawl4AI, Tavily
│   ├── schema.py           # Pydantic V2 models for structured data
│   ├── context.py          # Research context & dependency injection
│   └── scenarios.py        # Predefined research benchmarks
├── api/                    # FastAPI backend
│   ├── main.py             # App factory + lifespan
│   ├── database.py         # SQLite init & migrations
│   ├── db_sessions.py      # Session CRUD + checkpoint helpers
│   ├── stream.py           # SSE bridge (StreamingResearchContext)
│   └── routes/
│       ├── run.py          # POST /run, GET /run/{id}/stream, POST /run/{id}/retry
│       ├── sessions.py     # GET /sessions, GET /sessions/{id}
│       ├── export.py       # Report export endpoints
│       └── config.py       # Runtime configuration
├── web/                    # Next.js 16 frontend
│   ├── app/                # App Router pages
│   │   ├── page.tsx        # Home / query submission
│   │   ├── run/[id]/       # Live run view (SSE streaming)
│   │   ├── sessions/       # Session history browser
│   │   └── report/         # Final report viewer
│   ├── components/         # Shared UI components
│   ├── hooks/              # useRunSession (start-only), useLiveSession (refresh-safe SSE)
│   └── lib/
│       ├── api.ts          # Typed fetch wrappers
│       └── types.ts        # TypeScript types mirroring Python schema
├── tests/                  # Python tests (pytest)
├── pyproject.toml
└── .env.example
```

## Testing

```bash
# Python tests
uv run pytest tests/ -v

# Frontend tests
cd web && pnpm test
```
