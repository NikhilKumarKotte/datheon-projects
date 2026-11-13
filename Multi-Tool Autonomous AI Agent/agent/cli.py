"""Command Line Interface for Datheon Multi-Tool Autonomous Agent.

Supports interactive REPL mode, single-query direct execution, mock simulation,
and telemetry output.
"""

from __future__ import annotations

import sys
import argparse
from typing import Optional
from rich.prompt import Prompt

from agent.config import settings
from agent.core.models import get_llm
from agent.core.executor import AgentExecutor
from agent.tools import get_all_tools
from agent.ui.console import AgentConsole, console


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="agent",
        description="Datheon Multi-Tool Autonomous AI Agent",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-q", "--query",
        type=str,
        default=None,
        help="Single research query to execute directly (batch mode)",
    )
    parser.add_argument(
        "--repl",
        action="store_true",
        help="Launch interactive conversation REPL session (default if no query provided)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        choices=["openai", "google", "ollama", "mock"],
        default=None,
        help="Override LLM provider (openai, google, ollama, mock)",
    )
    parser.add_argument(
        "-m", "--model",
        type=str,
        default=None,
        help="Override model name (e.g. gpt-4o-mini, gemini-1.5-flash)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run in mock simulation mode (requires zero API keys, perfect for local demo/tests)",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=settings.max_iterations,
        help="Maximum autonomous tool execution steps",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress intermediate reasoning thought/action/observation panels",
    )
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the interactive Streamlit web interface in the browser",
    )
    return parser.parse_args(args)


def run_repl(executor: AgentExecutor, agent_ui: AgentConsole) -> None:
    """Run interactive continuous prompt session."""
    agent_ui.console.print("[dim]Enter your research query below. Type 'help' for examples, 'quit' to exit.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask("[bold green]Agent Query[/bold green]")
            clean_input = user_input.strip()

            if not clean_input:
                continue

            if clean_input.lower() in ("exit", "quit", ":q"):
                agent_ui.console.print("\n[bold yellow]👋 Exiting Datheon Autonomous Agent. Goodbye![/bold yellow]\n")
                break

            if clean_input.lower() in ("help", "?"):
                agent_ui.print_examples()
                continue

            if clean_input.lower() == "clear":
                agent_ui.console.clear()
                continue

            if clean_input.lower() == "tools":
                from rich.table import Table
                from rich.box import ROUNDED
                table = Table(title="Available Agent Tools", box=ROUNDED)
                table.add_column("Tool Name", style="bold magenta")
                table.add_column("Description", style="white")
                for t in executor.tools:
                    table.add_row(t.name, t.description or "")
                agent_ui.console.print(table)
                continue

            # Run query autonomously through agent executor
            executor.run(clean_input)

        except KeyboardInterrupt:
            agent_ui.console.print("\n[bold yellow]\nSession interrupted. Exiting...[/bold yellow]")
            break
        except Exception as exc:
            agent_ui.print_error(f"Unexpected error in REPL session: {str(exc)}")


def main(args: Optional[list] = None) -> int:
    """Main entrypoint for CLI execution."""
    parsed = parse_args(args)

    if parsed.web:
        from agent.web import launch_web_ui
        launch_web_ui()
        return 0

    agent_ui = AgentConsole()

    # Determine provider and model
    provider = "mock" if parsed.mock else (parsed.provider or settings.llm_provider)
    model = parsed.model or (settings.llm_model if provider != "mock" else "mock-autonomous-agent-v1")
    verbose = not parsed.quiet

    tools = get_all_tools()
    tool_names = [t.name for t in tools]

    # Show startup banner
    agent_ui.display_banner(
        provider=provider,
        model=model,
        tools=tool_names,
        base_dir=str(settings.file_reader_base_dir),
    )

    # Initialize LLM backend
    try:
        llm = get_llm(provider=provider, model_name=model)
    except Exception as init_err:
        agent_ui.print_error(
            f"Failed to initialize LLM provider '{provider}':\n{str(init_err)}"
        )
        agent_ui.console.print(
            "\n[bold yellow]💡 Tip:[/] You can run [bold cyan]python -m agent.main --mock[/] "
            "to test autonomous tool calling immediately without external API keys!\n"
        )
        return 1

    # Instantiate Agent Executor
    executor = AgentExecutor(
        llm=llm,
        tools=tools,
        console=agent_ui,
        max_iterations=parsed.max_steps,
        verbose=verbose,
    )

    # Execute single query if provided
    if parsed.query:
        result = executor.run(parsed.query)
        return 0 if result.is_success else 1

    # Otherwise enter interactive REPL
    run_repl(executor, agent_ui)
    return 0


if __name__ == "__main__":
    sys.exit(main())
