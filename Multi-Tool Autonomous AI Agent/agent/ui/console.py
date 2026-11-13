"""Professional Console Visualizer using Rich.

Formats the autonomous agent reasoning chain (Thought -> Action -> Observation -> Final Answer)
with clean alignments, cross-platform terminal compatibility, and telemetry panels.
"""

from __future__ import annotations

import sys
import time
from typing import Any, Dict, Optional, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from rich.box import ROUNDED, DOUBLE_EDGE, SIMPLE

# Reconfigure Windows stdout/stderr to UTF-8 with replace fallback
if sys.platform == "win32":
    try:
        if sys.stdout and hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    try:
        if sys.stderr and hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

console = Console(highlight=False, safe_box=True)


class AgentConsole:
    """Manages rich, humanized console outputs for the multi-tool autonomous agent."""

    def __init__(self, console_instance: Optional[Console] = None):
        self.console = console_instance or console

    def display_banner(
        self,
        provider: str,
        model: str,
        tools: List[str],
        base_dir: str,
        mode: str = "Autonomous Function-Calling",
    ) -> None:
        """Display startup banner with system configuration and tool status."""
        title_text = Text("[*] DATHEON MULTI-TOOL AUTONOMOUS AI AGENT", style="bold cyan")

        table = Table(box=ROUNDED, border_style="cyan", show_header=False, expand=True)
        table.add_column("Key", style="bold white", width=18)
        table.add_column("Value", style="cyan")

        table.add_row("LLM Provider", f"[bold green]{provider.upper()}[/] ({model})")
        table.add_row("Architecture", f"[bold yellow]{mode}[/] (ReAct reasoning loop)")
        table.add_row("Active Tools", ", ".join(f"[bold magenta]{t}[/]" for t in tools))
        table.add_row("Sandbox Root", f"[dim]{base_dir}[/]")
        table.add_row("Status", "[bold green][ONLINE] Ready for Compound Research Queries[/]")

        panel = Panel(
            table,
            title=title_text,
            subtitle="[dim]Type 'help' for examples | 'exit' or 'quit' to close[/dim]",
            border_style="bright_blue",
            padding=(1, 2),
        )
        self.console.print()
        self.console.print(panel)
        self.console.print()

    def print_query_header(self, query: str) -> None:
        """Display current user query in a highlighted panel."""
        self.console.print()
        self.console.print(
            Panel(
                Text(query, style="bold white"),
                title="[bold blue][USER QUERY][/]",
                border_style="blue",
                box=ROUNDED,
                padding=(0, 2),
            )
        )
        self.console.print()

    def print_thought(self, step: int, thought: str) -> None:
        """Display the agent's internal reasoning thought."""
        thought_clean = thought.strip()
        if not thought_clean:
            return

        panel_content = Text(thought_clean, style="italic yellow")
        self.console.print(
            Panel(
                panel_content,
                title=f"[bold yellow][STEP {step} | THOUGHT][/]",
                border_style="yellow",
                box=ROUNDED,
                padding=(0, 2),
            )
        )

    def print_action(self, tool_name: str, tool_args: Any) -> None:
        """Display the tool chosen by the agent and its input arguments."""
        import json

        if isinstance(tool_args, dict):
            try:
                args_str = json.dumps(tool_args, indent=2)
            except Exception:
                args_str = str(tool_args)
        else:
            args_str = str(tool_args)

        content = Text()
        content.append("Tool Invoked: ", style="dim")
        content.append(f"{tool_name}\n", style="bold magenta")
        content.append("Input Parameters:\n", style="dim")
        content.append(args_str, style="bright_cyan")

        self.console.print(
            Panel(
                content,
                title=f"[bold magenta][ACTION: {tool_name}][/]",
                border_style="magenta",
                box=ROUNDED,
                padding=(0, 2),
            )
        )

    def print_observation(self, observation: str, truncated_at: int = 1500) -> None:
        """Display the tool execution output / observation."""
        obs_clean = observation.strip()
        is_truncated = len(obs_clean) > truncated_at
        display_text = obs_clean[:truncated_at] + ("\n... [Observation Truncated for display] ..." if is_truncated else "")

        self.console.print(
            Panel(
                Text(display_text, style="white"),
                title="[bold cyan][OBSERVATION][/]",
                border_style="cyan",
                box=ROUNDED,
                padding=(0, 2),
            )
        )

    def print_final_answer(self, answer: str, duration_sec: float, steps: int) -> None:
        """Display the final synthesized answer and telemetry stats."""
        self.console.print()
        
        md_answer = Markdown(answer.strip())
        self.console.print(
            Panel(
                md_answer,
                title="[bold green][FINAL ANSWER][/]",
                border_style="green",
                box=DOUBLE_EDGE,
                padding=(1, 2),
            )
        )

        # Telemetry footer
        stats_text = (
            f"[dim]Execution Summary:[/] [bold cyan]{steps}[/] reasoning steps completed in "
            f"[bold green]{duration_sec:.2f}s[/] [dim]| Autonomous loop finished successfully[/]"
        )
        self.console.print(f"  {stats_text}\n")

    def print_error(self, message: str) -> None:
        """Display an error panel."""
        self.console.print(
            Panel(
                Text(message, style="bold red"),
                title="[bold red][ERROR][/]",
                border_style="red",
                box=ROUNDED,
                padding=(0, 2),
            )
        )

    def print_examples(self) -> None:
        """Print sample compound queries to demonstrate multi-tool autonomy."""
        table = Table(title="Suggested Multi-Step Compound Research Queries", box=ROUNDED, border_style="dim")
        table.add_column("Query Type", style="bold cyan", width=22)
        table.add_column("Example Prompt", style="white")

        table.add_row(
            "Local File + Math",
            "Read sample_data/q3_report.txt, find the Tokyo branch revenue, and calculate what percentage it is of total revenue."
        )
        table.add_row(
            "Local File + Web Search",
            "Read sample_data/tech_specs.md, check how many H100 GPUs we have, and search the web for current market specs of NVIDIA H100 SXM5."
        )
        table.add_row(
            "Inventory + Math",
            "Read sample_data/inventory.json and calculate the total inventory valuation by multiplying unit_cost by stock_quantity for all items."
        )
        table.add_row(
            "Web Search + Math",
            "Search the web for the current population of Tokyo and calculate what 12.5% of that population is."
        )
        self.console.print(table)
        self.console.print()
