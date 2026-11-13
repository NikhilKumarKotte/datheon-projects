"""Tests for CLI arguments and execution."""

import pytest
from agent.cli import parse_args, main


def test_cli_argument_parsing():
    args = parse_args(["--mock", "-q", "Calculate 15% of 100", "--quiet", "--web"])
    assert args.mock is True
    assert args.query == "Calculate 15% of 100"
    assert args.quiet is True
    assert args.web is True


def test_cli_direct_query_mock_execution():
    exit_code = main(["--mock", "-q", "Find Tokyo revenue in sample_data/q3_report.txt and calculate percentage", "--quiet"])
    assert exit_code == 0
