"""Real-time Web Search Tool using DuckDuckGo and optional Tavily fallback.

Designed for autonomous agents needing current, live information from the web.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _duckduckgo_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """Execute search using DuckDuckGo (via ddgs or duckduckgo_search)."""
    # Attempt to import either 'ddgs' (newer package name) or 'duckduckgo_search'
    DDGS_cls = None
    try:
        from ddgs import DDGS
        DDGS_cls = DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
            DDGS_cls = DDGS
        except ImportError as exc:
            raise RuntimeError(
                "Neither 'ddgs' nor 'duckduckgo_search' is installed. "
                "Install via 'pip install duckduckgo-search'."
            ) from exc

    results: List[Dict[str, str]] = []
    try:
        with DDGS_cls() as ddgs:
            raw_results = list(ddgs.text(query, max_results=max_results))
            for r in raw_results:
                results.append({
                    "title": r.get("title", "No Title"),
                    "href": r.get("href", r.get("link", "")),
                    "body": r.get("body", r.get("snippet", ""))
                })
    except Exception as e:
        logger.warning("DuckDuckGo search error: %s", e)
        raise

    return results


def _tavily_search(query: str, max_results: int = 5, api_key: Optional[str] = None) -> List[Dict[str, str]]:
    """Execute search using Tavily API if key is available."""
    import requests
    if not api_key:
        raise ValueError("TAVILY_API_KEY is not configured.")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
    }
    resp = requests.post(url, json=payload, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    results: List[Dict[str, str]] = []
    for r in data.get("results", []):
        results.append({
            "title": r.get("title", "No Title"),
            "href": r.get("url", ""),
            "body": r.get("content", "")
        })
    return results


@tool("web_search")
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web in real-time for live information, current events, facts, or data.

    Args:
        query: Search keywords or question to look up online.
        max_results: Maximum number of search results to retrieve (default is 5).

    Returns:
        A formatted markdown string containing search result titles, snippets, and URLs.
    """
    clean_query = query.strip().strip('"').strip("'")
    if not clean_query:
        return "Error: Empty search query provided."

    errors: List[str] = []

    # 1. Try DuckDuckGo Search first (no API key required)
    try:
        results = _duckduckgo_search(clean_query, max_results=max_results)
        if results:
            formatted = [f"### Web Search Results for: '{clean_query}'\n"]
            for idx, item in enumerate(results, start=1):
                formatted.append(
                    f"**{idx}. [{item['title']}]({item['href']})**\n"
                    f"{item['body']}\n"
                )
            return "\n".join(formatted)
        errors.append("DuckDuckGo returned 0 results.")
    except Exception as exc:
        errors.append(f"DuckDuckGo error: {str(exc)}")

    # 2. Try Tavily fallback if configured in settings
    try:
        from agent.config import settings
        if settings.tavily_api_key:
            results = _tavily_search(clean_query, max_results=max_results, api_key=settings.tavily_api_key)
            if results:
                formatted = [f"### Tavily Search Results for: '{clean_query}'\n"]
                for idx, item in enumerate(results, start=1):
                    formatted.append(
                        f"**{idx}. [{item['title']}]({item['href']})**\n"
                        f"{item['body']}\n"
                    )
                return "\n".join(formatted)
            errors.append("Tavily returned 0 results.")
    except Exception as exc:
        errors.append(f"Tavily error: {str(exc)}")

    return (
        f"Web search for '{clean_query}' could not return results.\n"
        f"Details: {'; '.join(errors)}"
    )
