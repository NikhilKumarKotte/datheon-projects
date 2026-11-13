"""
Realistic, pre-verified mock data for instant live review without requiring API quota.
Guarantees zero breaking runtime errors during offline review or demonstration.
"""

from typing import Any, Dict

MOCK_EXTRACTIONS: Dict[str, Dict[str, Any]] = {
    "invoice": {
        "invoice_number": "INV-1042",
        "seller": "ABC Technologies Inc.",
        "customer": "Ravi Kumar",
        "invoice_date": "2026-10-25",
        "due_date": "2026-11-25",
        "total_amount": 12500.0,
        "currency": "INR",
        "payment_status": "paid",
        "line_items": [
            {
                "description": "Wireless Mechanical Keyboard",
                "quantity": 2.0,
                "unit_price": 1500.0,
                "line_total": 3000.0,
            },
            {
                "description": "10-in-1 USB-C Multiport Dock",
                "quantity": 1.0,
                "unit_price": 9500.0,
                "line_total": 9500.0,
            },
        ],
    },
    "resume": {
        "full_name": "Nikhil Kumar",
        "email": "nikhil.kumar@example.com",
        "phone": "+91 98765 43210",
        "location": "Hyderabad, India",
        "professional_summary": "B.Tech AI/ML student and Python developer with strong expertise in FastAPI, LLM agents, and distributed backend systems.",
        "skills": [
            "Python",
            "FastAPI",
            "Pydantic",
            "SQL",
            "Docker",
            "PyTorch",
            "Pandas",
            "Streamlit",
            "Git",
        ],
        "education": [
            {
                "qualification": "B.Tech in Artificial Intelligence and Machine Learning",
                "institution": "Example Engineering College",
                "graduation_year": "2027",
                "score": "9.2 CGPA",
            }
        ],
        "experience": [
            {
                "job_title": "AI Engineering Intern",
                "company": "Cognitive Cloud Labs",
                "start_date": "2025-06",
                "end_date": "Present",
                "description": "Engineered automated structured document extraction pipeline achieving 99.4% precision.",
            }
        ],
        "projects": [
            {
                "name": "Structured LLM Extractor",
                "description": "Enterprise document processing pipeline using Gemini and Pydantic with agentic self-verification.",
                "technologies": ["Python", "FastAPI", "Gemini API", "Docker"],
            },
            {
                "name": "Food Price Comparison Platform",
                "description": "Real-time menu scraper and pricing intelligence service.",
                "technologies": ["Python", "Pandas", "Streamlit"],
            },
        ],
    },
    "receipt": {
        "merchant_name": "TARGET STORE #0821",
        "merchant_address": "1000 Nicollet Mall, Minneapolis, MN 55403",
        "merchant_phone": "(612) 555-0199",
        "transaction_date": "2026-10-26",
        "transaction_time": "14:32",
        "receipt_number": "884102",
        "subtotal_amount": 126.47,
        "tax_amount": 9.33,
        "tip_amount": 0.0,
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
            },
            {
                "description": "USB-C Braided Cable 2M",
                "quantity": 1.0,
                "price": 19.99,
                "category": "electronics",
            },
            {
                "description": "Energy Drink 16oz",
                "quantity": 1.0,
                "price": 2.99,
                "category": "beverage",
            },
            {
                "description": "Organic Dark Chocolate 85%",
                "quantity": 1.0,
                "price": 3.50,
                "category": "food",
            },
        ],
    },
}


def get_mock_extraction(document_type: str) -> Dict[str, Any]:
    """Retrieve pre-verified mock extraction data."""
    dt = document_type.lower().strip()
    return MOCK_EXTRACTIONS.get(dt, MOCK_EXTRACTIONS["invoice"])
