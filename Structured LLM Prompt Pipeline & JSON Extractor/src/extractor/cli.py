import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

from src.extractor.config import get_settings
from src.extractor.core.exceptions import ExtractorError
from src.extractor.core.service import ExtractorService
from src.extractor.schemas.registry import registry

logger = logging.getLogger("extractor.cli")


def build_parser() -> argparse.ArgumentParser:
    """Build and return command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="structured-extractor",
        description="Structured Document Extractor: Extract typed JSON from text using Gemini and Pydantic.",
    )

    # Extraction mode options
    extract_group = parser.add_argument_group("Extraction Options")
    extract_group.add_argument(
        "--type",
        "-t",
        choices=["auto"] + registry.list_types(),
        default="auto",
        help=f"Document schema type: 'auto' (autonomous classification) or {', '.join(registry.list_types())} (default: auto)",
    )
    extract_group.add_argument(
        "--input",
        "-i",
        help="Path to document file (PDF, Word DOCX, Image, Text, CSV)",
    )
    extract_group.add_argument(
        "--output",
        "-o",
        default="output.json",
        help="Path for saving validated JSON output (default: output.json)",
    )
    extract_group.add_argument(
        "--model",
        "-m",
        default=None,
        help="Gemini model name (default: from DEFAULT_MODEL in .env)",
    )
    extract_group.add_argument(
        "--demo",
        action="store_true",
        help="Run in offline deterministic Demo Mode (ideal for live reviews without API keys)",
    )

    # Server mode options
    server_group = parser.add_argument_group("Server Options")
    server_group.add_argument(
        "--serve",
        action="store_true",
        help="Launch the FastAPI REST API and interactive Web UI",
    )
    server_group.add_argument(
        "--host",
        default=None,
        help="Host to bind the web server to (default: 0.0.0.0)",
    )
    server_group.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind the web server to (default: 8000)",
    )
    server_group.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for local development",
    )

    # Utility options
    parser.add_argument(
        "--list-schemas",
        action="store_true",
        help="Print all registered document schemas and exit",
    )

    return parser


def run_server(host: Optional[str] = None, port: Optional[int] = None, reload: bool = False) -> None:
    """Launch the uvicorn ASGI server."""
    import uvicorn
    settings = get_settings()
    server_host = host or settings.server_host
    server_port = port or settings.server_port

    print(f"🚀 Starting Structured LLM Extractor server on http://{server_host}:{server_port}")
    print(f"📖 Interactive Swagger API Docs: http://{server_host}:{server_port}/docs")
    print(f"🖥️  Web UI Dashboard:            http://{server_host}:{server_port}/")
    uvicorn.run(
        "src.extractor.api.app:app",
        host=server_host,
        port=server_port,
        reload=reload,
    )


def list_schemas() -> None:
    """Display information about registered document types and schemas."""
    print("Registered Document Schemas:")
    for item in registry.get_metadata():
        print(f"\n  - [{item['type'].upper()}] - {item['title']}")
        print(f"    Description: {item['description']}")
        print(f"    Required Fields: {item['json_schema'].get('required', [])}")


def run_extraction(args: argparse.Namespace) -> None:
    """Execute document extraction from input file and save JSON output."""
    if not args.type:
        sys.exit("Error: --type is required for extraction. Use --help for usage or --list-schemas.")
    if not args.input:
        sys.exit("Error: --input is required for extraction. Specify a file path.")

    input_path = Path(args.input)
    if not input_path.exists():
        sys.exit(f"Error: Input file '{args.input}' not found.")

    settings = get_settings()
    service = ExtractorService(settings=settings)

    try:
        mode_str = " (DEMO MODE)" if args.demo else ""
        print(f"Extracting '{args.type}' from {args.input}{mode_str}...")
        result = service.extract(
            document=input_path,
            document_type=args.type,
            model_name=args.model,
            demo_mode=args.demo,
        )

        formatted_json = json.dumps(result.data, indent=2, ensure_ascii=False)
        output_path = Path(args.output)
        output_path.write_text(formatted_json + "\n", encoding="utf-8")

        print("\n--- Extracted Data ---")
        print(formatted_json)
        print("----------------------")
        print(f"[+] Saved validated JSON to: {output_path.resolve()}")
        print(
            f"[+] Metadata: Schema={result.metadata.document_type}, "
            f"Format={result.metadata.input_format}, "
            f"Model={result.metadata.model_used}, "
            f"Latency={result.metadata.duration_ms}ms"
        )
        if result.metadata.verification:
            v = result.metadata.verification
            print(f"[+] AI Verification: Confidence={int(v.confidence_score * 100)}%, Fields Detected={v.detected_fields_count}")
            if v.math_details:
                print(f"[+] Mathematical Consistency: {v.math_details}")
            if v.warnings:
                for w in v.warnings:
                    print(f"    [!] Note: {w}")

    except ExtractorError as exc:
        sys.exit(f"Extraction failed: {exc}")
    except Exception as exc:
        sys.exit(f"Unexpected error ({type(exc).__name__}): {exc}")


def main() -> None:
    """Main CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    if args.list_schemas:
        list_schemas()
        return

    if args.serve:
        run_server(host=args.host, port=args.port, reload=args.reload)
        return

    # If no serve or list-schemas flag, require extraction arguments
    if args.type or args.input:
        run_extraction(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
