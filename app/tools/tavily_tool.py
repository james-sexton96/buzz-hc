"""Tavily web search tool for broad search."""

import logging

from pydantic_ai import RunContext

from app.context import ResearchContext

logger = logging.getLogger(__name__)


async def tavily_search(
    ctx: RunContext[ResearchContext],
    query: str,
    max_results: int = 5,
    search_depth: str = "basic",
) -> str:
    """
    Run a Tavily web search and return a concatenated context string.

    Uses ResearchContext.tavily_api_key. If the key is missing or empty,
    returns a short message that Tavily is not configured.

    Args:
        ctx: Run context with ctx.deps.tavily_api_key.
        query: Search query.
        max_results: Max number of results to include (default 5).
        search_depth: 'basic' or 'advanced'.

    Returns:
        Summary string of search results, or error/placeholder message.
    """
    try:
        from tavily import AsyncTavilyClient
    except ImportError as e:
        logger.warning("tavily-python not available: %s", e)
        return f"Tavily unavailable: {e!s}"

    api_key = ctx.deps.tavily_api_key or ""
    if not api_key.strip():
        return "Tavily API key not set. Set TAVILY_API_KEY in environment and pass it via ResearchContext."

    try:
        ctx.deps.add_event("tool_call", "Tavily", f"Searching: {query}")
        client = AsyncTavilyClient(api_key=api_key)
        response = await client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
        )
        # Tavily SDK returns a plain dict, not a dataclass/object.
        results = _get(response, "results") or []
        ctx.deps.add_event("tool_result", "Tavily", f"Found {len(results)} results")
    except Exception as e:
        logger.exception("Tavily search failed: %s", e)
        return f"Tavily search error: {e!s}"

    if not results:
        return "No results from Tavily for this query."

    parts = []
    for r in results[:max_results]:
        title = _get(r, "title") or ""
        url = _get(r, "url") or ""
        content = _get(r, "content") or ""
        parts.append(f"## {title}\nURL: {url}\n\n{content}")
    return "\n\n".join(parts)


def _get(obj: object, key: str) -> object:
    """Get a value from a dict or object attribute — handles both."""
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)
