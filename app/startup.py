"""Pre-flight checks for runtime dependencies.

Called early in both entry points (main.py, app/ui.py) to catch missing
dependencies before agents start silently returning garbage results.
The big one: Playwright's Chromium binary, which Crawl4AI needs but
`uv sync` doesn't install.
"""

import os
import platform
import sys
from pathlib import Path


def _get_playwright_browsers_path() -> Path:
    """Resolve the Playwright browser cache directory.

    Respects PLAYWRIGHT_BROWSERS_PATH if set, otherwise uses the
    platform-specific default that Playwright has used since forever.
    """
    custom = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if custom:
        return Path(custom)

    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Caches" / "ms-playwright"
    elif system == "Windows":
        local_app = os.environ.get("LOCALAPPDATA", "")
        return Path(local_app) / "ms-playwright" if local_app else Path.home() / "ms-playwright"
    else:
        # Linux and everything else
        return Path.home() / ".cache" / "ms-playwright"


def _chromium_installed() -> bool:
    """Check whether a Playwright Chromium revision exists on disk."""
    browsers_path = _get_playwright_browsers_path()
    if not browsers_path.is_dir():
        return False
    # Playwright stores each browser as {name}-{revision}/
    return any(
        d.name.startswith("chromium-") and d.is_dir()
        for d in browsers_path.iterdir()
    )


def check_dependencies() -> None:
    """Validate that required runtime dependencies are in place.

    Checks (all warnings, nothing fatal — the app degrades gracefully):
      1. Playwright Chromium binary — deep_scrape won't work without it.
      2. .env file — you probably want your API keys.

    Call this before importing agents or doing any real work.
    """
    # --- Playwright Chromium ---
    if not _chromium_installed():
        print(
            "WARNING: Playwright Chromium browser is not installed.\n"
            "  deep_scrape will be unavailable — agents will fall back to other tools.\n"
            "  To enable it: uv run playwright install chromium\n",
            file=sys.stderr,
        )

    # --- .env file ---
    project_root = Path(__file__).resolve().parent.parent
    env_file = project_root / ".env"
    if not env_file.is_file():
        print(
            "WARNING: No .env file found. Copy .env.example → .env and add your API keys.\n",
            file=sys.stderr,
        )
