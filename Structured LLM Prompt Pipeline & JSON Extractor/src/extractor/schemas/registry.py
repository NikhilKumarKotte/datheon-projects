from typing import Any, Dict, List, Type
from src.extractor.schemas.base import StrictModel
from src.extractor.schemas.invoice import InvoiceData
from src.extractor.schemas.receipt import ReceiptData
from src.extractor.schemas.resume import ResumeData


class SchemaRegistry:
    """Central registry for document extraction schemas and metadata."""

    def __init__(self) -> None:
        self._registry: Dict[str, Type[StrictModel]] = {}
        self._descriptions: Dict[str, str] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(
            name="invoice",
            schema_cls=InvoiceData,
            description="Extracts invoice numbers, seller/buyer entities, line items, monetary totals, dates, and payment status.",
        )
        self.register(
            name="resume",
            schema_cls=ResumeData,
            description="Extracts candidate personal info, skills, education, work experience, and projects from resumes or CVs.",
        )
        self.register(
            name="receipt",
            schema_cls=ReceiptData,
            description="Extracts merchant details, purchase timestamps, line items, subtotal, sales tax, tip, total amount, and payment method from store receipts and expense slips.",
        )

    def register(self, name: str, schema_cls: Type[StrictModel], description: str = "") -> None:
        """Register a new schema type."""
        normalized_name = name.lower().strip()
        self._registry[normalized_name] = schema_cls
        self._descriptions[normalized_name] = description

    def get(self, name: str) -> Type[StrictModel]:
        """Retrieve schema class by type name."""
        normalized_name = name.lower().strip()
        if normalized_name not in self._registry:
            valid_types = ", ".join(self.list_types())
            raise KeyError(f"Unsupported document type '{name}'. Supported types: {valid_types}")
        return self._registry[normalized_name]

    def list_types(self) -> List[str]:
        """Return a sorted list of registered document type identifiers."""
        return sorted(list(self._registry.keys()))

    def get_metadata(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered schemas, including their JSON schemas."""
        metadata = []
        for name in self.list_types():
            cls = self._registry[name]
            metadata.append({
                "type": name,
                "title": cls.__name__,
                "description": self._descriptions.get(name, ""),
                "json_schema": cls.model_json_schema(),
            })
        return metadata


# Global registry singleton
registry = SchemaRegistry()
