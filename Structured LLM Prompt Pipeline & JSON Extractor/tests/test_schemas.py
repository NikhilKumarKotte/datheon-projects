import pytest
from pydantic import ValidationError

from src.extractor.schemas.invoice import InvoiceData, InvoiceLineItem
from src.extractor.schemas.receipt import ReceiptData, ReceiptLineItem
from src.extractor.schemas.registry import registry
from src.extractor.schemas.resume import EducationItem, ExperienceItem, ProjectItem, ResumeData


def test_invoice_line_item_valid():
    item = InvoiceLineItem(
        description="Software License",
        quantity=1.0,
        unit_price=49.99,
        line_total=49.99,
    )
    assert item.description == "Software License"
    assert item.quantity == 1.0
    assert item.line_total == 49.99


def test_invoice_line_item_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        InvoiceLineItem(
            description="Item",
            quantity=1.0,
            unauthorized_extra_field="malicious_or_hallucinated",
        )


def test_invoice_data_defaults():
    invoice = InvoiceData()
    assert invoice.payment_status == "unknown"
    assert invoice.line_items == []
    assert invoice.total_amount is None


def test_invoice_data_full_validation():
    data = {
        "invoice_number": "INV-2026-001",
        "seller": "Acme Corp",
        "customer": "Wayne Enterprises",
        "invoice_date": "2026-10-27",
        "due_date": "2026-11-27",
        "total_amount": 5000.0,
        "currency": "USD",
        "payment_status": "unpaid",
        "line_items": [
            {
                "description": "Cloud Hosting",
                "quantity": 10.0,
                "unit_price": 500.0,
                "line_total": 5000.0,
            }
        ],
    }
    model = InvoiceData.model_validate(data)
    assert model.invoice_number == "INV-2026-001"
    assert len(model.line_items) == 1
    assert model.line_items[0].line_total == 5000.0


def test_resume_data_validation():
    data = {
        "full_name": "Jane Doe",
        "email": "jane@example.com",
        "phone": "+1-555-0199",
        "location": "San Francisco, CA",
        "professional_summary": "Lead ML Engineer",
        "skills": ["Python", "PyTorch", "Kubernetes"],
        "education": [
            {
                "qualification": "M.S. in Computer Science",
                "institution": "Stanford University",
                "graduation_year": "2022",
                "score": "3.9 GPA",
            }
        ],
        "experience": [
            {
                "job_title": "Senior AI Engineer",
                "company": "DeepMind",
                "start_date": "2022",
                "end_date": "Present",
                "description": "Leading agentic coding research.",
            }
        ],
        "projects": [
            {
                "name": "Autonomous Agent",
                "description": "Agent framework for code generation",
                "technologies": ["Python", "FastAPI"],
            }
        ],
    }
    resume = ResumeData.model_validate(data)
    assert resume.full_name == "Jane Doe"
    assert "Python" in resume.skills
    assert resume.experience[0].company == "DeepMind"
    assert len(resume.projects) == 1


def test_receipt_data_validation():
    data = {
        "merchant_name": "Target Store #0821",
        "merchant_address": "1000 Nicollet Mall, Minneapolis, MN 55403",
        "merchant_phone": "(612) 555-0199",
        "transaction_date": "2026-10-26",
        "transaction_time": "14:32",
        "receipt_number": "884102",
        "subtotal_amount": 126.47,
        "tax_amount": 9.33,
        "tip_amount": None,
        "total_amount": 135.80,
        "currency": "USD",
        "payment_method": "credit_card",
        "card_last_four": "3194",
        "expense_category": "retail",
        "line_items": [
            {
                "description": "Logitech MX Master 3S Mouse",
                "quantity": 1.0,
                "price": 99.99,
                "category": "electronics",
            }
        ],
    }
    receipt = ReceiptData.model_validate(data)
    assert receipt.merchant_name == "Target Store #0821"
    assert receipt.total_amount == 135.80
    assert receipt.payment_method == "credit_card"
    assert receipt.card_last_four == "3194"
    assert len(receipt.line_items) == 1
    assert receipt.line_items[0].price == 99.99


def test_schema_registry():
    types = registry.list_types()
    assert "invoice" in types
    assert "resume" in types
    assert "receipt" in types

    invoice_cls = registry.get("invoice")
    assert invoice_cls == InvoiceData

    receipt_cls = registry.get("receipt")
    assert receipt_cls == ReceiptData

    metadata = registry.get_metadata()
    assert len(metadata) >= 3
    types_in_meta = [m["type"] for m in metadata]
    assert "invoice" in types_in_meta
    assert "resume" in types_in_meta
    assert "receipt" in types_in_meta
