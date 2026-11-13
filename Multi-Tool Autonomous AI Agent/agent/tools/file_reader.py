"""Secure Local File Reader Tool.

Provides sandboxed, line-numbered, and self-healing file inspection for autonomous agents.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, List
from langchain_core.tools import tool
from agent.config import settings


def _resolve_safe_path(path_str: str) -> Path:
    """Resolve file path and ensure it stays within the configured base directory sandbox."""
    base_dir = settings.file_reader_base_dir.resolve()
    target_path = Path(path_str)

    if not target_path.is_absolute():
        target_path = (base_dir / target_path).resolve()
    else:
        target_path = target_path.resolve()

    # Sandboxing check
    try:
        target_path.relative_to(base_dir)
    except ValueError:
        raise PermissionError(
            f"Security Violation: Access to path '{path_str}' is outside allowed base directory '{base_dir}'."
        )

    return target_path


def _find_similar_files(target_path: Path, max_suggestions: int = 5) -> List[str]:
    """Find existing files in the directory to suggest when a file is not found."""
    parent = target_path.parent
    if not parent.exists() or not parent.is_dir():
        # Fall back to base dir
        parent = settings.file_reader_base_dir.resolve()

    suggestions: List[str] = []
    try:
        for entry in parent.rglob("*"):
            if entry.is_file() and not any(part.startswith(".") for part in entry.parts):
                try:
                    rel = entry.relative_to(settings.file_reader_base_dir.resolve())
                    suggestions.append(str(rel))
                except ValueError:
                    suggestions.append(entry.name)
            if len(suggestions) >= max_suggestions:
                break
    except Exception:
        pass

    return suggestions


@tool("file_reader")
def file_reader(file_path: str, start_line: Optional[int] = 1, end_line: Optional[int] = None) -> str:
    """Read contents from a local file safely with line numbers and range slicing.

    Useful for analyzing local reports, specifications, source code, data files,
    or configurations stored in the workspace.

    Args:
        file_path: Path to the file to read (relative to workspace or project root).
        start_line: Optional 1-indexed line number to start reading from (default: 1).
        end_line: Optional 1-indexed line number to stop reading at (inclusive).

    Returns:
        Formatted file contents with line numbers, or a helpful diagnostic message.
    """
    clean_path = file_path.strip().strip('"').strip("'")
    if not clean_path:
        return "Error: No file_path provided to file_reader."

    try:
        resolved = _resolve_safe_path(clean_path)
    except PermissionError as perm_err:
        return f"Error: {str(perm_err)}"
    except Exception as exc:
        return f"Error resolving path '{clean_path}': {str(exc)}"

    if not resolved.exists():
        suggestions = _find_similar_files(resolved)
        msg = f"Error: File '{clean_path}' not found at '{resolved}'."
        if suggestions:
            msg += f"\nAvailable files in project:\n" + "\n".join(f"- {s}" for s in suggestions)
        return msg

    if not resolved.is_file():
        return f"Error: Path '{clean_path}' is a directory, not a readable file."

    # Check file size limit
    file_size = resolved.stat().st_size
    if file_size > settings.max_file_read_bytes:
        return (
            f"Error: File size ({file_size:,} bytes) exceeds maximum allowable limit "
            f"({settings.max_file_read_bytes:,} bytes). Use line ranges or inspect a smaller file."
        )

    # Read file lines with encoding fallback
    lines: List[str] = []
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    read_success = False

    for enc in encodings:
        try:
            with open(resolved, mode="r", encoding=enc) as f:
                lines = f.readlines()
            read_success = True
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f"Error reading file '{clean_path}': {str(e)}"

    if not read_success:
        return f"Error: Unable to decode file '{clean_path}' using standard text encodings."

    total_lines = len(lines)
    s_line = max(1, start_line or 1)
    e_line = min(total_lines, end_line or total_lines)

    if s_line > total_lines:
        return f"Error: start_line ({s_line}) exceeds total lines in file ({total_lines})."

    selected_lines = lines[s_line - 1 : e_line]
    output: List[str] = [
        f"--- File: {clean_path} (Lines {s_line}-{e_line} of {total_lines}) ---"
    ]
    for idx, line in enumerate(selected_lines, start=s_line):
        output.append(f"{idx:4d} | {line.rstrip()}")

    return "\n".join(output)
