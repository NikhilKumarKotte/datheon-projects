import io
import pytest
from pathlib import Path
from pypdf import PdfWriter
import docx

from src.extractor.core.document_loader import DocumentLoader, ProcessedDocument
from src.extractor.core.exceptions import EmptyDocumentError


def test_load_text_document():
    content = b"Invoice INV-1042\nSeller: Test Corp"
    doc = DocumentLoader.load_from_bytes(content, filename="invoice.txt")
    assert isinstance(doc, ProcessedDocument)
    assert doc.extension == ".txt"
    assert doc.mime_type == "text/plain"
    assert "Invoice INV-1042" in doc.text_content
    assert doc.is_multimodal is False
    assert doc.has_content is True


def test_load_empty_document_raises_error():
    with pytest.raises(EmptyDocumentError):
        DocumentLoader.load_from_bytes(b"", filename="empty.txt")

    with pytest.raises(EmptyDocumentError):
        DocumentLoader.load_from_bytes(b"   \n\t  ", filename="whitespace.txt")


def test_load_docx_document():
    # Build in-memory DOCX
    d = docx.Document()
    d.add_heading("Resume: Alex Mercer", level=0)
    d.add_paragraph("Full Stack Python Developer")
    table = d.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Skill"
    table.rows[0].cells[1].text = "Level"
    row = table.add_row().cells
    row[0].text = "FastAPI"
    row[1].text = "Expert"

    stream = io.BytesIO()
    d.save(stream)
    docx_bytes = stream.getvalue()

    doc = DocumentLoader.load_from_bytes(docx_bytes, filename="resume.docx")
    assert doc.extension == ".docx"
    assert "Resume: Alex Mercer" in doc.text_content
    assert "FastAPI" in doc.text_content
    assert doc.is_multimodal is False
    assert doc.has_content is True


def test_load_image_document():
    # 1x1 PNG transparent pixel
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    doc = DocumentLoader.load_from_bytes(png_bytes, filename="receipt.png")
    assert doc.extension == ".png"
    assert doc.mime_type == "image/png"
    assert doc.is_multimodal is True
    assert doc.binary_content == png_bytes
    assert doc.has_content is True


def test_load_pdf_document():
    # Generate in-memory PDF
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    stream = io.BytesIO()
    writer.write(stream)
    pdf_bytes = stream.getvalue()

    doc = DocumentLoader.load_from_bytes(pdf_bytes, filename="document.pdf")
    assert doc.extension == ".pdf"
    assert doc.mime_type == "application/pdf"
    assert doc.has_content is True
