"""Multi-Tool Autonomous AI Agent package.

Provides an autonomous agent engine capable of multi-step reasoning and invoking
real-time web search, math calculations, and local file reading tools.
"""

__version__ = "1.0.0"
__author__ = "Datheon AI Engineering Team"

from agent.config import settings
from agent.core.executor import AgentExecutor
from agent.tools import get_all_tools

__all__ = ["AgentExecutor", "get_all_tools", "settings", "__version__"]
