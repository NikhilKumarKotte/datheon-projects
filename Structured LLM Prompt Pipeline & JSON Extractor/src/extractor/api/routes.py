import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from src.extractor.config import Settings, get_settings
from src.extractor.core.exceptions import (
    EmptyDocumentError,
    ExtractorError,
    MissingAPIKeyError,
    ModelExecutionError,
    SchemaValidationError,
    UnsupportedDocumentTypeError,
)
from src.extractor.core.service import ExtractionResult, ExtractorService
from src.extractor.schemas.registry import registry

logger = logging.getLogger("extractor.api")
router = APIRouter()


class ExtractionRequest(BaseModel):
    """Payload for text extraction requests."""
    text: str = Field(
        ...,
        description="Raw document text to parse and extract structured data from",
        examples=["Invoice INV-1042\nSeller: ABC Technologies\nTotal: INR 12,500\nStatus: Paid"],
    )
    document_type: str = Field(
        default="auto",
        description="Type of document schema ('auto', 'invoice', 'resume', 'receipt')",
        examples=["auto"],
    )
    model: Optional[str] = Field(
        default=None,
        description="Optional Gemini model override (e.g. 'gemini-3.5-flash-lite')",
    )
    demo_mode: bool = Field(
        default=False,
        description="If True, runs in offline pre-verified demo mode with zero API key dependencies",
    )


class HealthResponse(BaseModel):
    """Application health and readiness status."""
    status: str
    version: str
    environment: str
    api_key_configured: bool
    default_model: str
    supported_schemas: List[str]


def get_extractor_service(settings: Settings = Depends(get_settings)) -> ExtractorService:
    """Dependency injector for ExtractorService."""
    return ExtractorService(settings=settings)


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Readiness and health check endpoint for container orchestrators and monitoring."""
    api_key = settings.gemini_api_key
    has_key = bool(api_key and api_key != "replace_with_your_api_key")

    return HealthResponse(
        status="healthy" if has_key else "degraded",
        version="1.0.0",
        environment=settings.environment,
        api_key_configured=has_key,
        default_model=settings.default_model,
        supported_schemas=registry.list_types(),
    )


@router.get("/api/v1/schemas", tags=["Schemas"])
def list_schemas() -> List[Dict[str, Any]]:
    """List all registered document types with their full JSON schemas and descriptions."""
    return registry.get_metadata()


@router.post("/api/v1/extract", response_model=ExtractionResult, tags=["Extraction"])
def extract_from_text(
    payload: ExtractionRequest,
    service: ExtractorService = Depends(get_extractor_service),
) -> ExtractionResult:
    """Extract structured data from raw text using schema constraints, auto-classification, and verification."""
    try:
        return service.extract(
            document_text=payload.text,
            document_type=payload.document_type,
            model_name=payload.model,
            demo_mode=payload.demo_mode,
        )
    except EmptyDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except MissingAPIKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{exc} Tip: You can pass demo_mode=True to test the full pipeline in offline review mode.",
        ) from exc
    except SchemaValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Schema validation failed: {exc}",
        ) from exc
    except ModelExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Extraction model failure: {exc}",
        ) from exc
    except ExtractorError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post("/api/v1/extract/upload", response_model=ExtractionResult, tags=["Extraction"])
async def extract_from_file_upload(
    file: UploadFile = File(..., description="Document file (PDF, DOCX, PNG, JPG, TXT, CSV, etc.)"),
    document_type: str = Form(default="auto", description="Schema type ('auto', 'invoice', 'resume', 'receipt')"),
    model: Optional[str] = Form(default=None, description="Optional model override"),
    demo_mode: bool = Form(default=False, description="Run in offline deterministic Demo Mode"),
    service: ExtractorService = Depends(get_extractor_service),
) -> ExtractionResult:
    """Extract structured data from any uploaded file format (PDF, Word DOCX, Image, Text, CSV, JSON)."""
    try:
        content_bytes = await file.read()
        return service.extract(
            document=content_bytes,
            document_type=document_type,
            model_name=model or None,
            filename=file.filename,
            demo_mode=demo_mode,
        )
    except EmptyDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except UnsupportedDocumentTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (MissingAPIKeyError, ModelExecutionError, SchemaValidationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
