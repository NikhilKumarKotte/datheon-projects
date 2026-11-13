"""Tool registry and exports for the Autonomous AI Agent."""

from typing import List
from langchain_core.tools import BaseTool
from agent.tools.web_search import web_search
from agent.tools.calculator import calculator
from agent.tools.file_reader import file_reader

ALL_TOOLS: List[BaseTool] = [
    web_search,
    calculator,
    file_reader,
]


def get_all_tools() -> List[BaseTool]:
    """Retrieve list of all registered agent tools."""
    return ALL_TOOLS.copy()


__all__ = ["web_search", "calculator", "file_reader", "get_all_tools", "ALL_TOOLS"]
