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

echo ""
echo "Done! Next steps:"
echo "  uv run python main.py                    # CLI mode"
echo "  uv run streamlit run app/ui.py           # Streamlit UI"
