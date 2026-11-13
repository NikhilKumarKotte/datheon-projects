import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from src.extractor.api.app import create_app
from src.extractor.config import Settings
from src.extractor.core.service import ExtractorService


@pytest.fixture
def mock_settings():
    """Return isolated test settings."""
    return Settings(
        gemini_api_key="test-api-key-12345",
        default_model="gemini-3.5-flash-lite",
        fallback_models=[],
        server_host="127.0.0.1",
        server_port=8000,
        environment="testing",
    )


@pytest.fixture
def mock_genai_client():
    """Create a mock genai.Client with customizable response."""
    client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"invoice_number": "TEST-123", "seller": "Test Seller", "customer": "Test Buyer", "invoice_date": "2026-01-01", "due_date": null, "total_amount": 100.0, "currency": "USD", "payment_status": "paid", "line_items": []}'
    client.models.generate_content.return_value = mock_response
    return client


@pytest.fixture
def mock_service(mock_settings, mock_genai_client):
    """Return an ExtractorService wired to mock GenAI client."""
    return ExtractorService(settings=mock_settings, client=mock_genai_client)


@pytest.fixture
def test_client(mock_service):
    """Return FastAPI TestClient with mocked extractor service."""
    from src.extractor.api.routes import get_extractor_service

    app = create_app()
    app.dependency_overrides[get_extractor_service] = lambda: mock_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
