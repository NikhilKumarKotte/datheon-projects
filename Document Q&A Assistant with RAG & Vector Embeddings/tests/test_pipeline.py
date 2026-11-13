"""
Unit tests for the end-to-end RAG Pipeline and citation verification.
"""

import pytest
from src.config import SAMPLE_DOCS_DIR
from src.document_loader import DocumentLoaderService
from src.text_splitter import TextChunkerService
from src.vector_store import VectorStoreManager
from src.rag_pipeline import RAGPipeline


@pytest.fixture(scope="module")
def initialized_rag():
    """Sets up an in-memory or persisted index of the sample handbook."""
    pdf_path = SAMPLE_DOCS_DIR / "acme_employee_handbook.pdf"
    docs = DocumentLoaderService.load_file(pdf_path)
    chunker = TextChunkerService(chunk_size=500, chunk_overlap=80)
    chunks = chunker.split_documents(docs)

    manager = VectorStoreManager()
    manager.create_or_add_documents(chunks, store_type="chroma")
    pipeline = RAGPipeline(vector_store_manager=manager)
    return pipeline


def test_rag_answers_remote_work_policy(initialized_rag):
    response = initialized_rag.answer_question(
        "What is the flexible remote work policy?",
        store_type="chroma",
        top_k=3,
    )
    assert response["answer"]
    assert "remote" in response["answer"].lower() or "hybrid" in response["answer"].lower()
    assert len(response["citations"]) >= 1

    # Verify citation points to page 1
    top_cite = response["citations"][0]
    assert top_cite["file_name"] == "acme_employee_handbook.pdf"
    assert top_cite["page"] == 1
    assert "acme_employee_handbook.pdf" in response["markdown_output"]


def test_rag_answers_vacation_policy(initialized_rag):
    response = initialized_rag.answer_question(
        "How many days of paid vacation do employees receive?",
        store_type="chroma",
        top_k=3,
    )
    assert "24" in response["answer"] or "vacation" in response["answer"].lower()
    assert len(response["citations"]) >= 1

    # Vacation is on Page 2
    pages = [c["page"] for c in response["citations"]]
    assert 2 in pages


def test_rag_answers_security_and_ai(initialized_rag):
    response = initialized_rag.answer_question(
        "What are the rules for generative AI and information security?",
        store_type="chroma",
        top_k=3,
    )
    assert len(response["citations"]) >= 1
    pages = [c["page"] for c in response["citations"]]
    # AI usage and info security are on Page 3
    assert 3 in pages


def test_rag_hallucination_guardrail(initialized_rag):
    """Verifies that out-of-scope questions are not hallucinated."""
    response = initialized_rag.answer_question(
        "What is the recipe for cooking Martian chocolate pancakes?",
        store_type="chroma",
        top_k=3,
    )
    # The pipeline must decline to answer
    assert "do not contain sufficient information" in response["answer"].lower() or "sorry" in response["answer"].lower()
