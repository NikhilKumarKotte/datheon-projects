import pytest

from src.extractor.core.exceptions import (
    EmptyDocumentError,
    MissingAPIKeyError,
    SchemaValidationError,
    UnsupportedDocumentTypeError,
)
from src.extractor.core.service import ExtractorService
from src.extractor.config import Settings


def test_empty_document_raises_error(mock_service):
    with pytest.raises(EmptyDocumentError):
        mock_service.extract("", "invoice")

    with pytest.raises(EmptyDocumentError):
        mock_service.extract("   \n\t  ", "invoice")


def test_unsupported_document_type_raises_error(mock_service):
    with pytest.raises(UnsupportedDocumentTypeError):
        mock_service.extract("Sample content", "unknown_type_xyz")


def test_missing_api_key_raises_error():
    empty_settings = Settings(gemini_api_key="")
    service = ExtractorService(settings=empty_settings)
    with pytest.raises(MissingAPIKeyError):
        service.extract("Invoice INV-1", "invoice")


def test_successful_mock_extraction(mock_service):
    result = mock_service.extract("Invoice INV-1042 Acme Corp", "invoice")
    assert result.metadata.document_type == "invoice"
    assert result.data["invoice_number"] == "TEST-123"
    assert result.data["seller"] == "Test Seller"
    assert result.metadata.duration_ms >= 0


def test_schema_validation_error_on_corrupt_response(mock_settings, mock_genai_client):
    # Setup response with extra field that violates StrictModel
    mock_response = mock_genai_client.models.generate_content.return_value
    mock_response.text = '{"invoice_number": "123", "hallucinated_field": "error"}'
    service = ExtractorService(settings=mock_settings, client=mock_genai_client)

    with pytest.raises(SchemaValidationError):
        service.extract("Some document", "invoice")
