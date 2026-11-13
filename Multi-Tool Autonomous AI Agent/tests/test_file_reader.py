"""Unit tests for the File Reader tool."""

from pathlib import Path
import pytest
from agent.tools.file_reader import file_reader


def test_read_existing_file():
    res = file_reader.invoke({"file_path": "sample_data/q3_report.txt", "start_line": 1, "end_line": 5})
    assert "ACME CORP" in res
    assert "1 |" in res
    assert "Lines 1-5" in res


def test_read_json_file():
    res = file_reader.invoke({"file_path": "sample_data/inventory.json"})
    assert "warehouse" in res
    assert "EDGE-GW-500" in res


def test_nonexistent_file_suggestions():
    res = file_reader.invoke({"file_path": "sample_data/unknown_file.txt"})
    assert "not found" in res
    # Should suggest existing files in the project
    assert "sample_data" in res or "q3_report.txt" in res


def test_sandbox_security_violation():
    # Attempt path traversal outside workspace root
    res = file_reader.invoke({"file_path": "../../Windows/System32/drivers/etc/hosts"})
    assert "Security Violation" in res or "Error" in res


def test_empty_path():
    res = file_reader.invoke({"file_path": "   "})
    assert "Error: No file_path provided" in res
