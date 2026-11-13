"""
Unit tests for TextChunkerService.
"""

import pytest
from langchain_core.documents import Document
from src.text_splitter import TextChunkerService


def test_chunker_basic_split():
    chunker = TextChunkerService(chunk_size=150, chunk_overlap=30)
    sample_text = (
        "Retrieval-Augmented Generation (RAG) is an architectural pattern that bridges large language models "
        "with external knowledge. By querying an external vector index before prompt submission, the model "
        "generates responses strictly grounded in verified context. This eliminates hallucinations and enables citations."
    )
    doc = Document(page_content=sample_text, metadata={"file_name": "test.pdf", "page": 1})

    chunks = chunker.split_documents([doc])
    assert len(chunks) > 1

    for chunk in chunks:
        assert "chunk_id" in chunk.metadata
        assert chunk.metadata["file_name"] == "test.pdf"
        assert chunk.metadata["page"] == 1
        assert "char_count" in chunk.metadata
        assert chunk.metadata["char_count"] <= 150


def test_chunker_statistics():
    chunker = TextChunkerService(chunk_size=200, chunk_overlap=40)
    docs = [
        Document(page_content="Sentence one. Sentence two.", metadata={"file_name": "a.txt", "page": 1}),
        Document(page_content="Another long paragraph with more information here.", metadata={"file_name": "b.txt", "page": 2}),
    ]
    chunks = chunker.split_documents(docs)
    stats = chunker.get_chunk_statistics(chunks)

    assert stats["total_chunks"] == len(chunks)
    assert stats["avg_chars"] > 0
    assert stats["min_chars"] > 0
    assert stats["max_chars"] >= stats["min_chars"]


def test_invalid_chunk_overlap():
    with pytest.raises(ValueError, match="must be greater than"):
        TextChunkerService(chunk_size=100, chunk_overlap=150)
