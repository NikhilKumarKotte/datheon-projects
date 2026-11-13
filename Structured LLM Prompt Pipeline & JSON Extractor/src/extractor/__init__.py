"""
Structured LLM Document Extractor
Enterprise-grade information extraction pipeline powered by Gemini and Pydantic.
"""

from src.extractor.config import Settings, get_settings
from src.extractor.core.service import ExtractorService, extract_document
from src.extractor.schemas.invoice import InvoiceData, InvoiceLineItem
from src.extractor.schemas.receipt import ReceiptData, ReceiptLineItem
from src.extractor.schemas.resume import EducationItem, ExperienceItem, ProjectItem, ResumeData

__version__ = "1.0.0"
__all__ = [
    "Settings",
    "get_settings",
    "ExtractorService",
    "extract_document",
    "InvoiceData",
    "InvoiceLineItem",
    "ReceiptData",
    "ReceiptLineItem",
    "ResumeData",
    "EducationItem",
    "ExperienceItem",
    "ProjectItem",
]
