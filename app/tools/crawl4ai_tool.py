"""Crawl4AI deep-scraping tool: bypass JS-heavy pharma portals and return clean Markdown."""

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def deep_scrape(url: str, query: str | None = None) -> str:
    """
    Scrape a URL and return its content as clean Markdown.

    Uses Crawl4AI's AsyncWebCrawler to handle JS-heavy pages (e.g. pharma portals).
    Optionally focus on content relevant to `query` (used for adaptive strategies).

    Args:
        url: Full URL to scrape.
        query: Optional query to guide extraction (e.g. for relevance filtering).

    Returns:
        Markdown string of the page content. Returns error message string on failure.
    """
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
    except ImportError as e:
        logger.warning("Crawl4AI not available: %s", e)
        return f"Scraping unavailable: {e!s}"

    try:
        browser_cfg = BrowserConfig(
            browser_type="chromium",
            headless=True,
            verbose=False,
        )
        run_cfg = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            word_count_threshold=10,
        )
        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url, config=run_cfg)
        if not result.success:
            return result.error_message or "Crawl failed with no message."
        md = getattr(result, "markdown", None)
        if md is None:
            md = getattr(result, "cleaned_html", "") or ""
        if hasattr(md, "raw_markdown"):
            return md.raw_markdown or ""
        if isinstance(md, str):
            return md
        return str(md)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        logger.exception("deep_scrape failed for %s", url)
        return f"Scraping error: {e!s}"
