"""LLM Factory and Model Initializer supporting multiple backends.

Supports:
- OpenAI (gpt-4o, gpt-4o-mini, etc.)
- Google Gemini (gemini-1.5-flash, gemini-2.0-flash, etc.)
- Ollama / Local OpenAI-compatible servers
- Mock / Simulation Mode for zero-key autonomous testing
"""

from __future__ import annotations

import os
import json
import logging
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from agent.config import settings

logger = logging.getLogger(__name__)


class MockAutonomousLLM(BaseChatModel):
    """Deterministic simulated LLM for testing the autonomous loop without external API keys.

    Analyzes conversation messages, detects missing tool information, generates
    realistic Thoughts and ToolCalls, and produces a final synthesized answer.
    """

    model_name: str = "mock-autonomous-agent-v1"

    @property
    def _llm_type(self) -> str:
        return "mock-autonomous"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Simulate autonomous multi-step reasoning."""
        # Find the original user query
        user_query = ""
        for m in messages:
            if isinstance(m, HumanMessage):
                user_query = str(m.content)

        # Inspect history of tool calls and tool responses
        tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]

        query_lower = user_query.lower()

        # Step 1: If no tools have been called yet
        if not tool_messages:
            # Check if query asks about file (e.g. q3_report, tech_specs, inventory)
            if "report" in query_lower or "q3" in query_lower or "tokyo" in query_lower:
                thought = (
                    "To answer this query, I first need to inspect the local financial report "
                    "in 'sample_data/q3_report.txt' to retrieve the Tokyo branch revenue figures."
                )
                tool_call = {
                    "name": "file_reader",
                    "args": {"file_path": "sample_data/q3_report.txt"},
                    "id": "call_mock_file_1",
                    "type": "tool_call",
                }
                msg = AIMessage(
                    content=f"Thought: {thought}",
                    tool_calls=[tool_call],
                )
                return ChatResult(generations=[ChatGeneration(message=msg)])

            elif "spec" in query_lower or "gpu" in query_lower or "h100" in query_lower or "cluster" in query_lower:
                thought = (
                    "I need to read the technical specifications from 'sample_data/tech_specs.md' "
                    "to extract the exact GPU count and cluster infrastructure details."
                )
                tool_call = {
                    "name": "file_reader",
                    "args": {"file_path": "sample_data/tech_specs.md"},
                    "id": "call_mock_file_tech",
                    "type": "tool_call",
                }
                msg = AIMessage(
                    content=f"Thought: {thought}",
                    tool_calls=[tool_call],
                )
                return ChatResult(generations=[ChatGeneration(message=msg)])

            elif "inventory" in query_lower or "stock" in query_lower or "sku" in query_lower:
                thought = (
                    "I should inspect the inventory JSON file at 'sample_data/inventory.json' "
                    "to gather the unit costs and stock quantities."
                )
                tool_call = {
                    "name": "file_reader",
                    "args": {"file_path": "sample_data/inventory.json"},
                    "id": "call_mock_inventory",
                    "type": "tool_call",
                }
                msg = AIMessage(
                    content=f"Thought: {thought}",
                    tool_calls=[tool_call],
                )
                return ChatResult(generations=[ChatGeneration(message=msg)])

            elif "search" in query_lower or "who is" in query_lower or "population" in query_lower or "weather" in query_lower:
                thought = (
                    "This query requires external or live information. I will search the web using DuckDuckGo."
                )
                tool_call = {
                    "name": "web_search",
                    "args": {"query": user_query, "max_results": 3},
                    "id": "call_mock_web_1",
                    "type": "tool_call",
                }
                msg = AIMessage(
                    content=f"Thought: {thought}",
                    tool_calls=[tool_call],
                )
                return ChatResult(generations=[ChatGeneration(message=msg)])

            else:
                # Default math or direct calculation
                thought = (
                    "The user's query requires mathematical evaluation. I will compute the expression with the calculator."
                )
                tool_call = {
                    "name": "calculator",
                    "args": {"expression": "48500000 * 0.20"},
                    "id": "call_mock_calc_default",
                    "type": "tool_call",
                }
                msg = AIMessage(
                    content=f"Thought: {thought}",
                    tool_calls=[tool_call],
                )
                return ChatResult(generations=[ChatGeneration(message=msg)])

        # Step 2: If we have 1 tool response
        if len(tool_messages) == 1:
            last_obs = str(tool_messages[-1].content)
            # If the last tool was file reader and query also asks for percentage, math, or calculation
            if ("percent" in query_lower or "calculate" in query_lower or "ratio" in query_lower or "total" in query_lower or "multiply" in query_lower):
                # Calculate ratio: 9,700,000 / 48,500,000 * 100 = 20.0%
                thought = (
                    "I have retrieved the necessary data from the local file. "
                    "Now, I must perform a precise mathematical calculation to determine the exact percentage."
                )
                tool_call = {
                    "name": "calculator",
                    "args": {"expression": "(9700000 / 48500000) * 100"},
                    "id": "call_mock_calc_2",
                    "type": "tool_call",
                }
                msg = AIMessage(
                    content=f"Thought: {thought}",
                    tool_calls=[tool_call],
                )
                return ChatResult(generations=[ChatGeneration(message=msg)])

            elif "search" in query_lower or "external" in query_lower or "market" in query_lower:
                thought = (
                    "Now that I have the local baseline numbers, I will search the web for market context."
                )
                tool_call = {
                    "name": "web_search",
                    "args": {"query": "NVIDIA H100 SXM5 specs memory bandwidth", "max_results": 3},
                    "id": "call_mock_web_market",
                    "type": "tool_call",
                }
                msg = AIMessage(
                    content=f"Thought: {thought}",
                    tool_calls=[tool_call],
                )
                return ChatResult(generations=[ChatGeneration(message=msg)])

        # Final Step: Synthesize Final Answer
        observations_summary = "\n".join(f"- Step {i+1}: {m.content[:200]}..." for i, m in enumerate(tool_messages))
        final_text = (
            f"### Research Synthesis & Findings\n\n"
            f"Based on autonomous multi-step investigation of your query: **'{user_query}'**:\n\n"
            f"1. **Primary Data Extraction**: Extracted key metrics and source observations.\n"
            f"2. **Computational Verification**: All calculations were verified using the calculator tool.\n"
            f"   - **Tokyo Revenue**: \\$9,700,000 USD\n"
            f"   - **Total Consolidated Revenue**: \\$48,500,000 USD\n"
            f"   - **Calculated Percentage**: **20.0%** of total revenue.\n\n"
            f"3. **Conclusion**: The autonomous multi-tool reasoning pipeline successfully verified "
            f"all intermediate steps without human intervention."
        )
        msg = AIMessage(content=final_text)
        return ChatResult(generations=[ChatGeneration(message=msg)])


def get_llm(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
) -> BaseChatModel:
    """Instantiate and return the configured LLM model backend."""
    prov = (provider or settings.llm_provider).lower()
    model = model_name or settings.llm_model
    temp = temperature if temperature is not None else settings.llm_temperature

    if prov == "mock":
        logger.info("Initializing Mock Autonomous LLM (dry-run simulation mode)")
        return MockAutonomousLLM()

    elif prov == "openai":
        api_key = settings.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set in environment or .env file.\n"
                "Please configure OPENAI_API_KEY in .env, or run with '--mock' to test without an API key."
            )
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            temperature=temp,
            api_key=api_key,
        )

    elif prov == "google":
        api_key = settings.google_api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY is not set in environment or .env file.\n"
                "Please configure GOOGLE_API_KEY in .env, or run with '--mock' to test without an API key."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=model if ("gemini" in model and model != "gemini-1.5-flash") else "gemini-3.8-flash",
            temperature=temp,
            google_api_key=api_key,
        )

    elif prov == "ollama":
        from langchain_openai import ChatOpenAI
        base_url = f"{settings.ollama_base_url.rstrip('/')}/v1"
        return ChatOpenAI(
            base_url=base_url,
            model=settings.ollama_model,
            temperature=temp,
            api_key="ollama",  # required dummy key by ChatOpenAI client
        )

    else:
        raise ValueError(
            f"Unsupported LLM provider '{prov}'. Supported: 'openai', 'google', 'ollama', 'mock'."
        )
