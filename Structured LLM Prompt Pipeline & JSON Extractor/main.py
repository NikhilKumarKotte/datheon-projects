"""
Structured LLM Document Extractor
Root entrypoint delegating to src.extractor.cli for CLI, web server, and extraction services.
"""

import sys
from pathlib import Path

# Add project root to sys.path to allow running directly from repository root
sys.path.insert(0, str(Path(__file__).parent))

from src.extractor.cli import main
from src.extractor.core.service import extract_document
from src.extractor.schemas.invoice import InvoiceData, InvoiceLineItem
from src.extractor.schemas.receipt import ReceiptData, ReceiptLineItem
from src.extractor.schemas.resume import ResumeData

__all__ = [
    "main",
    "extract_document",
    "InvoiceData",
    "InvoiceLineItem",
    "ReceiptData",
    "ReceiptLineItem",
    "ResumeData",
]

if __name__ == "__main__":
    main()
