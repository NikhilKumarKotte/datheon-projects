import io
import mimetypes
import os
from pathlib import Path
from typing import Optional, Union
from pydantic import BaseModel, Field

from src.extractor.core.exceptions import EmptyDocumentError, ExtractorError


class DocumentLoaderError(ExtractorError):
    """Raised when loading or parsing a document file fails."""
    pass


class ProcessedDocument(BaseModel):
    """Unified representation of a processed document ready for LLM extraction."""
    filename: Optional[str] = None
    extension: str = ""
    mime_type: str = "text/plain"
    text_content: Optional[str] = None
    binary_content: Optional[bytes] = Field(default=None, repr=False)
    is_multimodal: bool = False

    @property
    def has_content(self) -> bool:
        """Check if document contains either extractable text or binary multimodal payload."""
        if self.text_content and self.text_content.strip():
            return True
        return bool(self.binary_content and self.is_multimodal)


class DocumentLoader:
    """Universal document loader supporting PDF, Word (DOCX), Images, CSV, JSON, and Text."""

    IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff", ".gif"}
    TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".tsv", ".html", ".htm", ".xml", ".log", ".rtf"}

    @classmethod
    def load_from_path(cls, file_path: Union[str, Path]) -> ProcessedDocument:
        """Load and process a document file from filesystem path."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Document file not found: {path.resolve()}")
        if not path.is_file():
            raise ValueError(f"Path is not a regular file: {path.resolve()}")

        file_bytes = path.read_bytes()
        return cls.load_from_bytes(file_bytes=file_bytes, filename=path.name)

    @classmethod
    def load_from_bytes(cls, file_bytes: bytes, filename: Optional[str] = None) -> ProcessedDocument:
        """Parse raw file bytes into a ProcessedDocument based on filename or byte inspection."""
        if not file_bytes:
            raise EmptyDocumentError("Supplied document byte stream is empty.")

        name = filename or "document.txt"
        ext = Path(name).suffix.lower()

        # 1. PDF Documents (.pdf)
        if ext == ".pdf" or file_bytes.startswith(b"%PDF-"):
            return cls._process_pdf(file_bytes, filename=name)

        # 2. Word Documents (.docx)
        elif ext == ".docx":
            return cls._process_docx(file_bytes, filename=name)

        # 3. Image Files (.png, .jpg, .jpeg, etc.)
        elif ext in cls.IMAGE_EXTENSIONS or cls._is_image_bytes(file_bytes):
            return cls._process_image(file_bytes, filename=name, extension=ext)

        # 4. Text, Markdown, CSV, JSON, HTML, etc.
        else:
            return cls._process_text(file_bytes, filename=name, extension=ext)

    @classmethod
    def _process_pdf(cls, file_bytes: bytes, filename: str) -> ProcessedDocument:
        """Extract text from PDF pages; fall back to multimodal binary for scanned PDFs."""
        extracted_text_chunks = []
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(file_bytes))
            for page_idx, page in enumerate(reader.pages, start=1):
                page_text = page.extract_text() or ""
                cleaned = page_text.strip()
                if cleaned:
                    extracted_text_chunks.append(f"--- Page {page_idx} ---\n{cleaned}")
        except Exception as exc:
            # If pypdf fails (e.g. encrypted or complex stream), treat as multimodal binary for Gemini
            return ProcessedDocument(
                filename=filename,
                extension=".pdf",
                mime_type="application/pdf",
                binary_content=file_bytes,
                is_multimodal=True,
            )

        full_text = "\n\n".join(extracted_text_chunks).strip()

        # If substantial text was extracted, use text-based pipeline
        if len(full_text) >= 20:
            return ProcessedDocument(
                filename=filename,
                extension=".pdf",
                mime_type="application/pdf",
                text_content=full_text,
                is_multimodal=False,
            )

        # Scanned PDF or pure image PDF: send directly to Gemini multimodal vision
        return ProcessedDocument(
            filename=filename,
            extension=".pdf",
            mime_type="application/pdf",
            binary_content=file_bytes,
            is_multimodal=True,
        )

    @classmethod
    def _process_docx(cls, file_bytes: bytes, filename: str) -> ProcessedDocument:
        """Extract paragraphs and tables from Word (.docx) files."""
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            parts = []

            # 1. Extract paragraphs
            for paragraph in doc.paragraphs:
                text = paragraph.text.strip()
                if text:
                    parts.append(text)

            # 2. Extract tables (preserving table rows and columns)
            for table_idx, table in enumerate(doc.tables, start=1):
                table_lines = []
                for row in table.rows:
                    row_cells = [cell.text.strip() for cell in row.cells]
                    if any(row_cells):
                        table_lines.append(" | ".join(row_cells))
                if table_lines:
                    parts.append(f"\n[Table {table_idx}]\n" + "\n".join(table_lines))

            combined_text = "\n\n".join(parts).strip()
            if not combined_text:
                raise EmptyDocumentError(f"Word document '{filename}' contains no extractable text.")

            return ProcessedDocument(
                filename=filename,
                extension=".docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                text_content=combined_text,
                is_multimodal=False,
            )
        except EmptyDocumentError:
            raise
        except Exception as exc:
            raise DocumentLoaderError(f"Failed to read Word document '{filename}': {exc}") from exc

    @classmethod
    def _process_image(cls, file_bytes: bytes, filename: str, extension: str) -> ProcessedDocument:
        """Prepare image files for Gemini multimodal vision extraction."""
        mime_type, _ = mimetypes.guess_type(filename)
        if not mime_type or not mime_type.startswith("image/"):
            ext = extension.lstrip(".").lower()
            if ext in ["jpg", "jpeg"]:
                mime_type = "image/jpeg"
            elif ext == "png":
                mime_type = "image/png"
            elif ext == "webp":
                mime_type = "image/webp"
            else:
                mime_type = "image/png"

        return ProcessedDocument(
            filename=filename,
            extension=extension or ".png",
            mime_type=mime_type,
            binary_content=file_bytes,
            is_multimodal=True,
        )

    @classmethod
    def _process_text(cls, file_bytes: bytes, filename: str, extension: str) -> ProcessedDocument:
        """Decode plain text, markdown, CSV, JSON, HTML with encoding fallbacks."""
        text = None
        for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
            try:
                text = file_bytes.decode(enc)
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise DocumentLoaderError(f"Could not decode text in '{filename}' with supported encodings.")

        cleaned = text.strip()
        if not cleaned:
            raise EmptyDocumentError(f"Document '{filename}' is empty.")

        mime_type, _ = mimetypes.guess_type(filename)
        return ProcessedDocument(
            filename=filename,
            extension=extension or ".txt",
            mime_type=mime_type or "text/plain",
            text_content=cleaned,
            is_multimodal=False,
        )

    @staticmethod
    def _is_image_bytes(data: bytes) -> bool:
        """Inspect magic bytes to detect common image file signatures."""
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return True
        if data.startswith(b"\xff\xd8\xff"):
            return True
        if data.startswith(b"RIFF") and b"WEBP" in data[:16]:
            return True
        if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
            return True
        return False
