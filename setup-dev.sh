#!/bin/bash
# One-command dev environment setup for Buzz-HC.
# Run this after cloning — it handles the stuff that's easy to forget.
set -e

echo "==> Installing Python dependencies..."
uv sync

echo "==> Installing Playwright browsers for Crawl4AI..."
uv run playwright install chromium

echo "==> Checking for .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "    Created .env from .env.example — edit it with your API keys."
else
    echo "    .env already exists, skipping."
fi

echo "==> Installing Next.js dependencies..."
if command -v pnpm &>/dev/null; then
    (cd web && pnpm install)
else
    echo "    pnpm not found — install it with: npm install -g pnpm"
fi

echo ""
echo "Done! Next steps:"
echo "  uv run uvicorn api.main:app --reload     # FastAPI backend (port 8000)"
echo "  cd web && pnpm dev                       # Next.js frontend (port 3000)"
echo ""
echo "  uv run python main.py                    # CLI mode"
echo "  uv run streamlit run app/ui.py           # Streamlit UI (legacy)"
echo ""
echo "  uv run pytest tests/ -v                  # Python tests"
echo "  cd web && pnpm test                      # Frontend tests"
