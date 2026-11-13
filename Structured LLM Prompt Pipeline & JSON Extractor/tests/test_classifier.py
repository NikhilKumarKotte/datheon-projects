import pytest
from src.extractor.core.classifier import DocumentClassifier
from src.extractor.core.service import ExtractorService
from src.extractor.config import Settings


def test_classifier_by_filename():
    assert DocumentClassifier.classify("generic text", filename="my_resume_2026.pdf") == "resume"
    assert DocumentClassifier.classify("generic text", filename="Tax_Invoice_1042.pdf") == "invoice"
    assert DocumentClassifier.classify("generic text", filename="grocery_receipt.png") == "receipt"


def test_classifier_by_text_resume():
    text = """
    Jane Doe
    Summary: Senior Software Engineer
    Education: B.S. Computer Science from Stanford University
    Experience: 5 years at Google building distributed ML systems
    Skills: Python, Go, Kubernetes, PyTorch
    Projects: Autonomous Agents
    """
    assert DocumentClassifier.classify(text) == "resume"


def test_classifier_by_text_invoice():
    text = """
    INVOICE
    Invoice No: INV-2026-991
    Bill To: ACME Corporation
    Due Date: 2026-12-01
    Unit Price: $100.00
    Grand Total: $500.00
    Payment Terms: Net 30
    """
    assert DocumentClassifier.classify(text) == "invoice"


def test_classifier_by_text_receipt():
    text = """
    STORE RECEIPT
    Store #4412
    Cashier: John
    Subtotal: $24.50
    Tax: $1.96
    Tip: $3.00
    Total: $29.46
    Visa ending in 4122
    Change Due: $0.00
    """
    assert DocumentClassifier.classify(text) == "receipt"


def test_classifier_fallback_defaults_to_invoice():
    # Content with zero identifiable signals
    assert DocumentClassifier.classify("lorem ipsum dolor sit amet") == "invoice"


def test_service_demo_mode_auto_classification():
    # ExtractorService in demo_mode should succeed without any API key or client
    settings = Settings(gemini_api_key="")
    service = ExtractorService(settings=settings)

    resume_text = "Education: B.Tech in CS. Experience: Software Engineer. Skills: Python, FastAPI."
    result = service.extract(resume_text, document_type="auto", demo_mode=True)

    assert result.metadata.document_type == "resume"
    assert result.data["full_name"] == "Nikhil Kumar"
    assert result.verification.confidence_score >= 0.90
    assert result.metadata.is_demo is True
