import pytest
from src.extractor.core.verification import VerificationAgent, VerificationReport


def test_verification_invoice_perfect_math():
    data = {
        "invoice_number": "INV-101",
        "invoice_date": "2026-10-25",
        "total_amount": 100.0,
        "line_items": [
            {"description": "Item 1", "quantity": 2.0, "unit_price": 30.0, "line_total": 60.0},
            {"description": "Item 2", "quantity": 1.0, "unit_price": 40.0, "line_total": 40.0},
        ],
    }
    report = VerificationAgent.audit_extraction("invoice", data)
    assert isinstance(report, VerificationReport)
    assert report.math_verified is True
    assert "perfectly equals" in report.math_details
    assert len(report.warnings) == 0
    assert report.confidence_score >= 0.95


def test_verification_invoice_math_discrepancy():
    data = {
        "invoice_number": "INV-102",
        "invoice_date": "2026-10-25",
        "total_amount": 50.0,  # Grand total declared as 50, but items sum to 100
        "line_items": [
            {"description": "Item 1", "quantity": 1.0, "unit_price": 100.0, "line_total": 100.0},
        ],
    }
    report = VerificationAgent.audit_extraction("invoice", data)
    assert report.math_verified is False
    assert "Discrepancy" in report.math_details
    assert any("exceeds declared total" in w for w in report.warnings)
    assert report.confidence_score < 0.95


def test_verification_invoice_missing_identifiers():
    data = {
        "total_amount": 100.0,
        "line_items": [],
    }
    report = VerificationAgent.audit_extraction("invoice", data)
    assert any("Invoice identifier" in w for w in report.warnings)
    assert any("Invoice date" in w for w in report.warnings)


def test_verification_receipt_math():
    data = {
        "merchant_name": "Starbucks",
        "subtotal_amount": 10.0,
        "tax_amount": 1.0,
        "tip_amount": 2.0,
        "total_amount": 13.0,
    }
    report = VerificationAgent.audit_extraction("receipt", data)
    assert report.math_verified is True
    assert "matches total" in report.math_details
    assert len(report.warnings) == 0
    assert report.confidence_score >= 0.95


def test_verification_resume_warnings():
    incomplete_resume = {
        "full_name": None,
        "email": None,
        "phone": None,
        "skills": [],
    }
    report = VerificationAgent.audit_extraction("resume", incomplete_resume)
    assert any("full name" in w for w in report.warnings)
    assert any("contact method" in w for w in report.warnings)
    assert any("Skills section" in w for w in report.warnings)
    assert report.confidence_score < 0.90
