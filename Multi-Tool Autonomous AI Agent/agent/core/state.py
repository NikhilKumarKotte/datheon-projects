"""Agent State and Execution Telemetry tracking."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StepRecord(BaseModel):
    """Record of an individual reasoning step."""
    step_number: int
    thought: Optional[str] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Any] = None
    observation: Optional[str] = None
    duration_seconds: float = 0.0


class AgentRunResult(BaseModel):
    """Encapsulates the final outcome and complete telemetry of an agent query run."""
    query: str
    final_answer: str
    steps: List[StepRecord] = Field(default_factory=list)
    total_duration_seconds: float = 0.0
    is_success: bool = True
    error_message: Optional[str] = None
