"""Integration tests for the Autonomous Agent Executor loop."""

import pytest
from agent.core.models import MockAutonomousLLM
from agent.core.executor import AgentExecutor
from agent.tools import get_all_tools
from agent.ui.console import AgentConsole


def test_agent_executor_compound_query_run():
    """Test full multi-step compound query with mock autonomous LLM."""
    mock_llm = MockAutonomousLLM()
    tools = get_all_tools()
    ui = AgentConsole()

    executor = AgentExecutor(
        llm=mock_llm,
        tools=tools,
        console=ui,
        verbose=False,  # quiet during automated tests
    )

    query = "Read sample_data/q3_report.txt, find Tokyo branch revenue, and calculate what percentage it is of total revenue."
    result = executor.run(query)

    assert result.is_success is True
    assert result.final_answer != ""
    assert "Tokyo" in result.final_answer or "20" in result.final_answer

    # Verify that multi-step reasoning steps were recorded
    assert len(result.steps) >= 2
    tool_names_called = [s.tool_name for s in result.steps]
    assert "file_reader" in tool_names_called
    assert "calculator" in tool_names_called

    # Verify telemetry
    assert result.total_duration_seconds >= 0.0
    for step in result.steps:
        assert step.duration_seconds >= 0.0
        assert step.thought is not None
        assert step.observation is not None


def test_agent_executor_empty_query():
    mock_llm = MockAutonomousLLM()
    executor = AgentExecutor(llm=mock_llm, verbose=False)
    result = executor.run("   ")
    assert result.is_success is False
