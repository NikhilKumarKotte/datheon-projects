"""Autonomous Agent Executor implementing the ReAct reasoning loop.

Binds LangChain tools to an LLM and manages the multi-step execution loop:
Thought -> Action -> Action Input -> Observation -> Final Answer.
"""

from __future__ import annotations

import time
import logging
from typing import List, Dict, Any, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool

from agent.config import settings
from agent.core.prompt import SYSTEM_PROMPT
from agent.core.models import get_llm
from agent.core.state import StepRecord, AgentRunResult
from agent.tools import get_all_tools
from agent.ui.console import AgentConsole

logger = logging.getLogger(__name__)


class AgentExecutor:
    """Executes multi-step autonomous reasoning with tools."""

    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        tools: Optional[List[BaseTool]] = None,
        console: Optional[AgentConsole] = None,
        max_iterations: Optional[int] = None,
        verbose: bool = True,
    ):
        self.console = console or AgentConsole()
        self.verbose = verbose
        self.max_iterations = max_iterations or settings.max_iterations

        # Initialize tools
        self.tools = tools if tools is not None else get_all_tools()
        self.tool_map: Dict[str, BaseTool] = {t.name: t for t in self.tools}

        # Initialize LLM backend
        self.llm = llm or get_llm()

        # Bind tools to the LLM (LangChain function/tool calling protocol)
        try:
            self.model_with_tools = self.llm.bind_tools(self.tools)
        except Exception as e:
            logger.warning("Could not bind tools natively with bind_tools: %s. Using raw LLM.", e)
            self.model_with_tools = self.llm

    def run(
        self,
        query: str,
        on_thought: Optional[Any] = None,
        on_action: Optional[Any] = None,
        on_observation: Optional[Any] = None,
        on_final_answer: Optional[Any] = None,
    ) -> AgentRunResult:
        """Run the autonomous agent loop to solve a compound research query."""
        clean_query = query.strip()
        if not clean_query:
            return AgentRunResult(
                query=query,
                final_answer="No query provided.",
                is_success=False,
                error_message="Empty query",
            )

        if self.verbose:
            self.console.print_query_header(clean_query)

        messages: List[BaseMessage] = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=clean_query),
        ]

        steps: List[StepRecord] = []
        start_time = time.perf_counter()
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            step_start = time.perf_counter()

            try:
                # 1. Invoke the LLM with current conversation state
                ai_response: AIMessage = self.model_with_tools.invoke(messages)
            except Exception as llm_err:
                err_msg = f"LLM Invocation Failed: {str(llm_err)}"
                if self.verbose:
                    self.console.print_error(err_msg)
                total_duration = time.perf_counter() - start_time
                return AgentRunResult(
                    query=clean_query,
                    final_answer=f"Error encountered: {err_msg}",
                    steps=steps,
                    total_duration_seconds=total_duration,
                    is_success=False,
                    error_message=err_msg,
                )

            # Extract thought from content if present
            raw_content = ""
            if isinstance(ai_response.content, str):
                raw_content = ai_response.content
            elif isinstance(ai_response.content, list):
                # Some providers return structured text blocks
                text_parts = [
                    block.get("text", "") if isinstance(block, dict) else str(block)
                    for block in ai_response.content
                ]
                raw_content = "\n".join(text_parts)

            # Check if tools were requested
            tool_calls = getattr(ai_response, "tool_calls", []) or []

            # Display thought if present
            thought_text = raw_content.strip()
            if thought_text and tool_calls:
                # Strip "Thought:" prefix if already formatted
                display_thought = thought_text
                if display_thought.lower().startswith("thought:"):
                    display_thought = display_thought[8:].strip()
                if self.verbose:
                    self.console.print_thought(step=iteration, thought=display_thought)
                if on_thought:
                    try:
                        on_thought(iteration, display_thought)
                    except Exception:
                        pass

            # If no tool calls, the agent has reached its Final Answer!
            if not tool_calls:
                total_duration = time.perf_counter() - start_time
                final_answer = raw_content or "No final answer produced."
                
                # Format final answer display
                if self.verbose:
                    self.console.print_final_answer(
                        answer=final_answer,
                        duration_sec=total_duration,
                        steps=iteration,
                    )
                if on_final_answer:
                    try:
                        on_final_answer(final_answer, total_duration, iteration)
                    except Exception:
                        pass

                return AgentRunResult(
                    query=clean_query,
                    final_answer=final_answer,
                    steps=steps,
                    total_duration_seconds=total_duration,
                    is_success=True,
                )

            # Append the assistant's decision to message history
            messages.append(ai_response)

            # 2. Execute requested tool calls (Actions)
            for tool_call in tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", f"call_{iteration}_{tool_name}")

                if self.verbose:
                    self.console.print_action(tool_name=tool_name, tool_args=tool_args)
                if on_action:
                    try:
                        on_action(tool_name, tool_args)
                    except Exception:
                        pass

                # Tool invocation
                if tool_name not in self.tool_map:
                    observation = (
                        f"Error: Tool '{tool_name}' does not exist. "
                        f"Available tools are: {list(self.tool_map.keys())}"
                    )
                else:
                    target_tool = self.tool_map[tool_name]
                    try:
                        observation = target_tool.invoke(tool_args)
                    except Exception as tool_err:
                        observation = f"Error executing tool '{tool_name}': {str(tool_err)}"

                if self.verbose:
                    self.console.print_observation(observation=str(observation))
                if on_observation:
                    try:
                        on_observation(tool_name, str(observation))
                    except Exception:
                        pass

                # Record step telemetry
                step_record = StepRecord(
                    step_number=iteration,
                    thought=thought_text,
                    tool_name=tool_name,
                    tool_input=tool_args,
                    observation=str(observation),
                    duration_seconds=time.perf_counter() - step_start,
                )
                steps.append(step_record)

                # Append tool observation to conversation history for next iteration
                messages.append(
                    ToolMessage(
                        content=str(observation),
                        tool_call_id=tool_id,
                        name=tool_name,
                    )
                )

        # Loop limit reached without natural termination
        total_duration = time.perf_counter() - start_time
        fallback_msg = (
            f"Agent reached maximum limit of {self.max_iterations} reasoning steps.\n"
            "Summary of observations gathered:\n"
            + "\n".join(f"- Step {s.step_number} ({s.tool_name}): {s.observation[:120]}..." for s in steps)
        )
        if self.verbose:
            self.console.print_error(fallback_msg)

        return AgentRunResult(
            query=clean_query,
            final_answer=fallback_msg,
            steps=steps,
            total_duration_seconds=total_duration,
            is_success=False,
            error_message="Max iterations reached",
        )
