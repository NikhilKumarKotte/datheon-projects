"""
Unit tests for VectorStoreManager (ChromaDB & FAISS).
"""

import shutil
from pathlib import Path
import pytest
from langchain_core.documents import Document
from src.vector_store import VectorStoreManager
from src.embeddings import EmbeddingFactory

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_store_data"
TEST_CHROMA_DIR = TEST_DATA_DIR / "chroma"
TEST_FAISS_DIR = TEST_DATA_DIR / "faiss"


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_dirs():
    """Ensure clean test environment before and after test execution."""
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)
    TEST_CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    TEST_FAISS_DIR.mkdir(parents=True, exist_ok=True)
    yield
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR, ignore_errors=True)


def test_chroma_and_faiss_indexing_and_retrieval():
    embeddings = EmbeddingFactory.get_embeddings(provider="huggingface")
    manager = VectorStoreManager(
        chroma_dir=TEST_CHROMA_DIR,
        faiss_dir=TEST_FAISS_DIR,
        embeddings=embeddings,
    )

    sample_chunks = [
        Document(
            page_content="Employees receive a one-time home office equipment stipend of $1,200 USD.",
            metadata={"file_name": "handbook.pdf", "page": 1, "chunk_id": "c1"},
        ),
        Document(
            page_content="Acme provides 24 days of paid vacation per calendar year.",
            metadata={"file_name": "handbook.pdf", "page": 2, "chunk_id": "c2"},
        ),
        Document(
            page_content="All company laptops must enforce full-disk encryption and multi-factor authentication.",
            metadata={"file_name": "handbook.pdf", "page": 3, "chunk_id": "c3"},
        ),
    ]

    # Test ChromaDB Indexing
    manager.create_or_add_documents(sample_chunks, store_type="chroma")
    chroma_stats = manager.get_stats(store_type="chroma")
    assert chroma_stats["is_indexed"] is True
    assert chroma_stats["vector_count"] >= 3

    # Test ChromaDB Retrieval
    chroma_results = manager.similarity_search_with_confidence(
        "home office equipment stipend", k=1, store_type="chroma"
    )
    assert len(chroma_results) == 1
    doc, conf = chroma_results[0]
    assert "$1,200" in doc.page_content
    assert doc.metadata["page"] == 1
    assert 0.0 <= conf <= 1.0

    # Test FAISS Indexing
    manager.create_or_add_documents(sample_chunks, store_type="faiss")
    faiss_stats = manager.get_stats(store_type="faiss")
    assert faiss_stats["is_indexed"] is True
    assert faiss_stats["vector_count"] == 3

    # Test FAISS Retrieval
    faiss_results = manager.similarity_search_with_confidence(
        "paid vacation days", k=1, store_type="faiss"
    )
    assert len(faiss_results) == 1
    doc_f, conf_f = faiss_results[0]
    assert "24 days" in doc_f.page_content
    assert doc_f.metadata["page"] == 2
    assert 0.0 <= conf_f <= 1.0
