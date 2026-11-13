import sys
from unittest.mock import patch

from src.extractor.cli import build_parser, main


def test_cli_parser_defaults():
    parser = build_parser()
    args = parser.parse_args(["--type", "invoice", "--input", "sample.txt"])
    assert args.type == "invoice"
    assert args.input == "sample.txt"
    assert args.output == "output.json"


def test_cli_list_schemas_invocation(capsys):
    with patch.object(sys, "argv", ["structured-extractor", "--list-schemas"]):
        main()
    captured = capsys.readouterr()
    assert "Registered Document Schemas:" in captured.out
    assert "INVOICE" in captured.out
    assert "RESUME" in captured.out
