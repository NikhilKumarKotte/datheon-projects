"""Unit tests for the Web Search tool."""

from unittest.mock import patch, MagicMock
import pytest
from agent.tools.web_search import web_search


def test_empty_query():
    res = web_search.invoke({"query": "   "})
    assert "Error: Empty search query" in res


def test_mocked_duckduckgo_search():
    mock_results = [
        {"title": "Test Title 1", "href": "https://example.com/1", "body": "Snippet 1 text"},
        {"title": "Test Title 2", "href": "https://example.com/2", "body": "Snippet 2 text"},
    ]
    with patch("agent.tools.web_search._duckduckgo_search", return_value=mock_results):
        res = web_search.invoke({"query": "artificial intelligence agents", "max_results": 2})
        assert "Web Search Results" in res
        assert "Test Title 1" in res
        assert "Snippet 1 text" in res
        assert "https://example.com/1" in res


def test_web_search_error_handling():
    with patch("agent.tools.web_search._duckduckgo_search", side_effect=Exception("Network Timeout")):
        res = web_search.invoke({"query": "test query"})
        assert "could not return results" in res
        assert "Network Timeout" in res
