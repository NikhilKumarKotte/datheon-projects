"""
Domain-specific exceptions for the extraction pipeline.
"""


class ExtractorError(Exception):
    """Base exception for all extractor errors."""
    pass


class EmptyDocumentError(ExtractorError):
    """Raised when the input document text is empty or only whitespace."""
    pass


class MissingAPIKeyError(ExtractorError):
    """Raised when the Gemini API key is missing or invalid."""
    pass


class UnsupportedDocumentTypeError(ExtractorError):
    """Raised when an requested document type is not in the schema registry."""
    pass


class ModelExecutionError(ExtractorError):
    """Raised when the underlying LLM fails or returns an unparseable response."""
    pass


class SchemaValidationError(ExtractorError):
    """Raised when model output fails local Pydantic validation."""
    pass
