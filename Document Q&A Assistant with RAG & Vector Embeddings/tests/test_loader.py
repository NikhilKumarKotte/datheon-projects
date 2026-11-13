"""
Unit tests for DocumentLoaderService.
"""

import pytest
from pathlib import Path
from src.document_loader import DocumentLoaderService
from src.config import SAMPLE_DOCS_DIR


def test_load_pdf_document():
    pdf_path = SAMPLE_DOCS_DIR / "acme_employee_handbook.pdf"
    assert pdf_path.exists(), f"Sample PDF does not exist at {pdf_path}"

    docs = DocumentLoaderService.load_file(pdf_path)
    assert len(docs) == 3, f"Expected 3 pages, found {len(docs)}"

    for idx, doc in enumerate(docs, 1):
        assert doc.metadata["page"] == idx
        assert doc.metadata["file_name"] == "acme_employee_handbook.pdf"
        assert doc.metadata["file_type"] == "pdf"
        assert len(doc.page_content) > 50


def test_load_txt_document():
    txt_path = SAMPLE_DOCS_DIR / "rag_system_architecture.txt"
    assert txt_path.exists()

    docs = DocumentLoaderService.load_file(txt_path)
    assert len(docs) == 1
    assert docs[0].metadata["page"] == 1
    assert docs[0].metadata["file_type"] == "txt"
    assert "Retrieval-Augmented Generation" in docs[0].page_content


def test_unsupported_file_format():
    with pytest.raises(ValueError, match="Unsupported file format"):
        DocumentLoaderService.load_file(__file__)  # .py is not supported
